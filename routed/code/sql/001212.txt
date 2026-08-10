


--  @version $Id: //product/DCS/version/11.3/templates/DCS/sql/dcs_content_mgmt_ddl.xml#1 $$Change: 1385662 $
-- This file contains create table statements, which will configure your database for use with the Content Management schema.

create table dcs_wcm_media_rltd_prod (
	media_id	varchar2(40)	not null,
	sequence_num	integer	not null,
	related_product_id	varchar2(40)	not null
,constraint wcm_media_rltd_product_p primary key (media_id,sequence_num)
,constraint wcm_media_rltd_product1_f foreign key (media_id) references wcm_media_content (id)
,constraint wcm_media_rltd_product2_f foreign key (related_product_id) references dcs_product (product_id));

create index wcm_media_rltd_product_idx on dcs_wcm_media_rltd_prod (related_product_id);

create table dcs_wcm_media_rltd_ctgy (
	media_id	varchar2(40)	not null,
	sequence_num	integer	not null,
	related_category_id	varchar2(40)	not null
,constraint wcm_media_rltd_category_p primary key (media_id,sequence_num)
,constraint wcm_media_rltd_category1_f foreign key (media_id) references wcm_media_content (id)
,constraint wcm_media_rltd_category_f foreign key (related_category_id) references dcs_category (category_id));

create index wcm_media_rltd_category_idx on dcs_wcm_media_rltd_ctgy (related_category_id);

create table dcs_wcm_article_rltd_prod (
	article_id	varchar2(40)	not null,
	sequence_num	integer	not null,
	related_product_id	varchar2(40)	not null
,constraint wcm_article_rltd_product_p primary key (article_id,sequence_num)
,constraint wcm_article_rltd_product1_f foreign key (article_id) references wcm_article (id)
,constraint wcm_article_rltd_product2_f foreign key (related_product_id) references dcs_product (product_id));

create index wcm_article_rltd_product_idx on dcs_wcm_article_rltd_prod (related_product_id);

create table dcs_wcm_article_rltd_ctgy (
	article_id	varchar2(40)	not null,
	sequence_num	integer	not null,
	related_category_id	varchar2(40)	not null
,constraint wcm_article_rltd_category_p primary key (article_id,sequence_num)
,constraint wcm_article_rltd_category1_f foreign key (article_id) references wcm_article (id)
,constraint wcm_article_rltd_category2_f foreign key (related_category_id) references dcs_category (category_id));

create index wcm_article_rltd_category_idx on dcs_wcm_article_rltd_ctgy (related_category_id);



