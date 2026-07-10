# Enron Emails Recommended Analysis Views

These are logical DuckDB views worth using as named starting points. They are
not materialized in the DoxaBase capsule; the capsule records their row counts,
caveats, and rationale.

## Plausible-Date Message Views

```sql
create or replace view eml_messages_plausible_1997_2004 as
select *
from eml_messages
where date >= timestamp '1997-01-01'
  and date < timestamp '2005-01-01';
```

Observed row count: 1,210,548.

```sql
create or replace view xml_messages_plausible_1997_2004 as
select *
from xml_messages
where date_sent >= timestamp '1997-01-01'
  and date_sent < timestamp '2005-01-01';
```

Observed row count: 1,203,416.

## Representation Comparison Views

```sql
create or replace view eml_xml_doc_id_overlap as
select e.doc_id
from eml_messages e
join xml_messages x using (doc_id);
```

Observed row count: 1,227,255.

```sql
create or replace view eml_only_blank_source_subset as
select e.*
from eml_messages e
anti join xml_messages x using (doc_id)
where e.folder = ''
  and e.source_file = '';
```

Observed row count: 7,132.

## Text-Ready Views

```sql
create or replace view eml_messages_with_body_text as
select *
from eml_messages
where body != '';
```

Observed row count: 739,872.

```sql
create or replace view eml_messages_with_body_top_text as
select *
from eml_messages
where body_top != '';
```

Observed row count: 695,225.

## Sender-Email Coverage Views

```sql
create or replace view eml_messages_with_regex_sender_email as
select *
from eml_messages
where from_email is not null
  and regexp_matches(from_email, '[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+\\.[A-Za-z]{2,}');
```

Observed row count: 97,929.

```sql
create or replace view xml_messages_with_regex_sender_email as
select *
from xml_messages
where from_ is not null
  and regexp_matches(from_, '[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+\\.[A-Za-z]{2,}');
```

Observed row count: 198,050.

## Message-Like Plausible-Date Views

These exclude `calendar`, `contacts`, and `meetings` folder families after the
date filter. They are useful for ordinary message-text or communication-network
analyses, but the exclusion rule should be cited.

```sql
create or replace view eml_messages_plausible_message_like as
select *
from eml_message_folder_families
where date >= timestamp '1997-01-01'
  and date < timestamp '2005-01-01'
  and folder_family not in ('calendar', 'contacts', 'meetings');
```

Observed row count: 980,561.

```sql
create or replace view eml_messages_plausible_message_like_with_body as
select *
from eml_messages_plausible_message_like
where body != '';
```

Observed row count: 714,325.

```sql
create or replace view eml_messages_plausible_message_like_with_body_top as
select *
from eml_messages_plausible_message_like
where body_top != '';
```

Observed row count: 670,649.

```sql
create or replace view xml_messages_plausible_message_like as
select *
from xml_message_location_families
where date_sent >= timestamp '1997-01-01'
  and date_sent < timestamp '2005-01-01'
  and folder_family not in ('calendar', 'contacts', 'meetings');
```

Observed row count: 973,356.

## Message Attachment Count Views

```sql
create or replace view eml_message_attachment_counts as
select
  m.doc_id,
  coalesce(count(a.parent_doc_id), 0) as attachment_rows
from eml_messages m
left join eml_attachments a
  on a.parent_doc_id = m.doc_id
group by 1;
```

```sql
create or replace view xml_message_attachment_counts as
select
  m.doc_id,
  coalesce(count(a.parent_doc_id), 0) as attachment_rows
from xml_messages m
left join xml_attachments a
  on a.parent_doc_id = m.doc_id
group by 1;
```

Both attachment-count views have a maximum of 260 attachment rows per message;
4,525 messages have 10 or more attachment rows in each representation.

## Folder Family Views

```sql
create or replace view eml_message_folder_families as
select
  case
    when folder = '' then 'blank'
    else lower(regexp_extract(folder, '^\\\\?([^\\\\]+)', 1))
  end as folder_family,
  *
from eml_messages;
```

```sql
create or replace view xml_message_location_families as
select
  case
    when location_uri = '' then 'blank'
    else lower(regexp_extract(location_uri, '^[^\\\\]+\\\\([^\\\\]+)', 1))
  end as folder_family,
  *
from xml_messages;
```

## Monthly Volume View

Use folder-family fields when plotting monthly volume. The largest observed
EML/XML month, 2002-11, is dominated by calendar rows.

```sql
create or replace view eml_monthly_volume_by_folder_family as
select
  folder_family,
  strftime(date, '%Y-%m') as month,
  count(*) as rows,
  count(distinct custodian) as custodians,
  sum(case when body != '' then 1 else 0 end) as body_populated_rows,
  sum(case when has_attachments then 1 else 0 end) as messages_with_attachments
from eml_message_folder_families
where date >= timestamp '1997-01-01'
  and date < timestamp '2005-01-01'
group by 1, 2;
```
