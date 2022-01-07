# -*- coding: utf-8 -*-
import pymysql.cursors
import pymysql
import pyodbc
import os
from scrapy.conf import settings
import urllib2
import numbers
import re
from decimal import Decimal
import json, requests


mysql_enabled = False
if settings.get("MYSQL_ENABLE") and settings.get("MYSQL_ENABLE") != "False":
    mysql_enabled = True
mysql_update = settings.get("MYSQL_UPDATE")

if mysql_enabled:
    columns = []
    tablename = settings.get("MYSQL_TABLENAME")

    # db = pymysql.connect(
    #     host = settings.get("MYSQL_HOSTNAME"),
    #     user = settings.get("MYSQL_USERNAME"),
    #     password = settings.get("MYSQL_PASSWORD"),
    #     db = settings.get("MYSQL_DATABASE"),
    #     charset = 'utf8mb4',
    #     cursorclass = pymysql.cursors.DictCursor
    # )
    # with db.cursor() as cursor:
    #     sql = """SELECT column_name
    #         FROM information_schema.columns
    #         WHERE table_schema = %(database)s
    #         AND table_name = %(tablename)s"""
    #     cursor.execute(sql, dict(
    #         database = settings.get("MYSQL_DATABASE"),
    #         tablename = tablename
    #     ))
    #     columns = set([v.get("column_name") for v in cursor.fetchall()])

    # /////////////////////////sql server////////////////////////////////////////
    user = settings.get("MYSQL_USERNAME"),
    password = settings.get("MYSQL_PASSWORD"),
    db = settings.get("MYSQL_DATABASE"),
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                      "Server=localhost;"
                      "Database=%s;"
                      "Trusted_Connection=yes;"%(db))
                        # UID=sa;PWD=sa



# for row in cursor:
#     print('row = %r' % (row,))

def parse_money(money):
    if money is None or isinstance(money, numbers.Number):
        return money
    money = (u""+money).replace(",", ".")
    money = money.replace(".", "", money.count(".") - 1)
    money = re.sub("[^\d.]", "", money)
    money = Decimal(money)
    money = round(money, 2)
    return money


def download_image(image_url, image_path):
    if not image_url or os.path.isfile(image_path):
        return

    try:
        r = requests.get(image_url, stream=True)
        with open(image_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
    except Exception as e:
        print e
        print "Error downloading file."

def save_item(item, spider):
    global columns
    tablename = spider.name
    try:
        with cnxn.cursor() as cursor:
            if mysql_update:
                sql = "UPDATE {} SET price='{}', old_price='{}', discount='{}' WHERE url='{}'"\
                    .format(tablename, item['price'], item['old_price'], item['discount'], item['url'])
                result = cursor.execute(sql)
                # print result
                cnxn.commit()
            else:
                # sql = """INSERT IGNORE INTO {tablename}
                #     (`id`,`ean`, `url`, `name`, `category`, `price`, `old_price`, `currency`, `discount`, `brand_name`, `image_url`, `image_path`, `found_on`, `specs`, `sub_category`)
                # VALUES
                #     (%(id)s,
                #     %(ean)s,
                #     %(url)s,
                #     %(name)s,
                #     %(category)s,
                #     %(price)s,
                #     %(old_price)s,
                #     %(currency)s,
                #     %(discount)s,
                #     %(brand_name)s,
                #     %(image_url)s,
                #     %(image_path)s,
                #     %(found_on)s,
                #     %(specs)s,
                #     %(sub_category)s
                #     )
                # """.format(tablename=tablename)
                key_txt = ','.join(item.keys()).lower()
                values = ""
                for val in item.values():
                    if isinstance(val,float) or isinstance(val,int):
                        val = str(val)
                    else:
                        if val == None:
                            val = "''"
                        else:
                            val = "'" + val + "'"
                    values = values + ',' + val
                values = values[1:]

                # values = str(','.join(item.values())).encode('utf-8')
                sql = "INSERT INTO %s (%s) VALUES (%s)"%(tablename, key_txt, values)

                cursor.execute(sql)
                cnxn.commit()

                # product_id = item.get("id")
                # specs_columns = [key for key in item if key.startswith("specs_")]
                #
                # for column in specs_columns:
                #     if column not in columns:
                #         sql = "ALTER TABLE {tablename} ADD `{columnname}` TEXT".format(tablename = tablename, columnname = column)
                #         cursor.execute(sql)
                #         columns.add(column)
                #         db.commit()
                #
                # if len(specs_columns):
                #     sql = "UPDATE {tablename} SET {set_fields} WHERE id={product_id}".format(
                #         tablename = tablename,
                #         set_fields = ", ".join("`{0}`=%({0})s".format(k) for k in specs_columns),
                #         product_id = product_id)
                #     cursor.execute(sql, item)
                #     db.commit()
    except Exception as error:
        print "Error Inserting Item"
        print str(error)
        # print json.dumps(item, indent=4)


class AlbarounPipeline(object):

    def process_item(self, item, spider):
        for k in item:
            if item[k] is None:
                item[k] = ""

        item["price"] = parse_money(item["price"])
        if item["old_price"] and spider.name != 'xcite':
            item["old_price"] = parse_money(item["old_price"])

        if mysql_update == False:
            # item["title"] = item["title"].strip()
            image_url = item["image_url"]
            image_path = ""

            if settings.get("DOWNLOAD_IMAGES"):
                filename, ext = os.path.splitext(image_url)
                image_directory = settings.get("IMAGE_DIRECTORY")
                image_path = "{}/{}/{}{}".format(image_directory,spider.name, item["ean"].replace('/', '_'), ext)

                if not os.path.exists("{}/{}/".format(image_directory,spider.name)):
                    os.makedirs("{}/{}/".format(image_directory,spider.name))
                download_image(image_url, image_path)

            item["image_path"] = image_path

        # if mysql_enabled:
        #     save_item(item, spider)

        return item
