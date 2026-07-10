# Enron Emails Query Cookbook

These are non-secret starter query shapes for the DoxaBase Enron email store.
Use the DoxaBase query-planning helpers first when choosing a storage route:
`describe_query_context()` and `draft_query_plan()`.

The examples assume DuckDB can read the Parquet objects at `s3://enron-emails/`.
Configure the local MinIO endpoint and credentials outside the query text.

## Register Tables

```sql
create or replace view eml_messages as
select * from read_parquet('s3://enron-emails/eml_messages.parquet');

create or replace view eml_attachments as
select * from read_parquet('s3://enron-emails/eml_attachments.parquet');

create or replace view xml_messages as
select * from read_parquet('s3://enron-emails/xml_messages.parquet');

create or replace view xml_attachments as
select * from read_parquet('s3://enron-emails/xml_attachments.parquet');
```

## Choose A Message Surface

Use `eml_messages` when body/body_top text is needed. Use `xml_messages` when
native hashes, native paths, text paths, and XML-derived metadata are central.
Join them by `doc_id` only after deciding how to treat the XML subset.

```sql
select
  count(*) as eml_rows,
  count(distinct doc_id) as eml_doc_ids
from eml_messages;

select
  count(*) as xml_rows,
  count(distinct doc_id) as xml_doc_ids
from xml_messages;

select count(*) as eml_only_rows
from eml_messages e
anti join xml_messages x using (doc_id);
```

## Apply Date Hygiene

Use an explicit analysis window. The DoxaBase store records severe date
outliers, especially in XML `date_sent`.

```sql
where date >= timestamp '1997-01-01'
  and date < timestamp '2005-01-01'
```

For XML:

```sql
where date_sent >= timestamp '1997-01-01'
  and date_sent < timestamp '2005-01-01'
```

## Attachment Joins

Use `parent_doc_id -> doc_id`.

```sql
select
  m.doc_id,
  m.custodian,
  count(a.parent_doc_id) as attachment_rows
from eml_messages m
left join eml_attachments a
  on a.parent_doc_id = m.doc_id
group by 1, 2;
```

For exact XML attachment counts, aggregate `xml_attachments`; do not rely only
on `xml_messages.attachment_count`.

```sql
select
  m.doc_id,
  coalesce(count(a.parent_doc_id), 0) as counted_attachment_rows,
  coalesce(m.attachment_count, 0) as declared_attachment_count
from xml_messages m
left join xml_attachments a
  on a.parent_doc_id = m.doc_id
group by 1, 3
having counted_attachment_rows != declared_attachment_count;
```

## Sender And Recipient Domains

Regex extraction is useful but incomplete. XML fields often contain display
names or Exchange/X.500-style names. Treat extraction coverage as a quality
metric before building a network.

```sql
select
  lower(regexp_extract(from_email, '@([^> ]+)', 1)) as sender_domain,
  count(*) as rows
from eml_messages
where from_email is not null
  and from_email != ''
group by 1
order by rows desc;
```

## Text Surface Choice

`body_top` removes quoted-history markers in the observed profile, but it is
blank for more rows than `body`. Choose deliberately.

```sql
select
  count(*) as rows,
  sum(case when body = '' then 1 else 0 end) as blank_body_rows,
  sum(case when body_top = '' then 1 else 0 end) as blank_body_top_rows,
  sum(case when body_top = body then 1 else 0 end) as body_top_equals_body_rows,
  sum(case when length(body_top) < length(body) then 1 else 0 end) as body_top_shorter_rows
from eml_messages;
```

## Threading And Deduplication

Do not use `message_id` as a unique key. For conversation work, combine
`message_id`, `subject_clean`, `reply_depth`, folder/custodian context, and
possibly text hashes.

```sql
select
  count(*) as rows,
  count(distinct doc_id) as distinct_doc_ids,
  count(distinct message_id) as distinct_message_ids
from eml_messages;

select message_id, count(*) as rows
from eml_messages
group by 1
having count(*) > 1
order by rows desc;
```

## Attachment Type Analysis

Normalize extension case and handle blanks.

```sql
select
  lower(regexp_extract(filename, '\\.([A-Za-z0-9]+)$', 1)) as extension,
  count(*) as rows
from eml_attachments
group by 1
order by rows desc;
```

XML attachments have `native_hash`, which is useful for duplicate-content
analysis.

```sql
select native_hash, count(*) as rows
from xml_attachments
group by 1
having count(*) > 1
order by rows desc;
```
