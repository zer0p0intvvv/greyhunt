# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#
# 声明：本代码仅供学习和研究目的使用。

"""
小红书爬虫独立入口

用法:
    # 搜索模式（关键词搜索）
    uv run main.py --lt qrcode --type search --keywords "抖音号出售" --save_data_option sqlite

    # 详情模式（指定笔记 ID）
    uv run main.py --lt qrcode --type detail --specified_id <note_id1>,<note_id2>

    # 创作者模式（爬取指定用户主页）
    uv run main.py --lt qrcode --type creator --creator_id <user_id>

    # 开启评论爬取
    uv run main.py --lt qrcode --type search --keywords "闲置号" --get_comment true --get_sub_comment true

    # 初始化数据库
    uv run main.py --init_db sqlite

登录方式: qrcode | phone | cookie
存储格式: sqlite | jsonl | csv | json | excel | mongodb
"""

import asyncio
import sys

import typer

import config
from cmd_arg.arg import parse_cmd
from database.db import init_db
from media_platform.xhs import XiaoHongShuCrawler
from var import crawler_type_var

app = typer.Typer()


@app.command()
def main(
    lt: str = typer.Option("qrcode", help="登录方式: qrcode | phone | cookie"),
    type: str = typer.Option("search", help="爬取类型: search | detail | creator"),
    keywords: str = typer.Option("", help="搜索关键词，多个用逗号分隔"),
    specified_id: str = typer.Option("", help="笔记 ID 列表，多个用逗号分隔"),
    creator_id: str = typer.Option("", help="创作者 ID"),
    cookies: str = typer.Option("", help="Cookie 字符串（cookie 登录方式使用）"),
    save_data_option: str = typer.Option("sqlite", help="存储方式: sqlite | jsonl | csv | json | excel"),
    save_data_path: str = typer.Option("", help="文件存储路径（默认 data/）"),
    get_comment: bool = typer.Option(True, help="是否爬取评论"),
    get_sub_comment: bool = typer.Option(True, help="是否爬取子评论"),
    crawler_max_notes_count: int = typer.Option(20, help="最大爬取笔记数"),
    init_db: str = typer.Option("", help="初始化数据库: sqlite | mysql | postgres"),
):
    if init_db:
        asyncio.run(_init_db(init_db))
        return

    # 写入全局配置
    config.LOGIN_TYPE = lt
    config.CRAWLER_TYPE = type
    config.PLATFORM = "xhs"
    config.KEYWORDS = keywords
    config.SPECIFIED_ID_LIST = [i.strip() for i in specified_id.split(",") if i.strip()]
    config.XHS_CREATOR_ID_LIST = [creator_id] if creator_id else []
    config.COOKIES = cookies
    config.SAVE_DATA_OPTION = save_data_option
    if save_data_path:
        config.SAVE_DATA_PATH = save_data_path
    config.ENABLE_GET_COMMENTS = get_comment
    config.ENABLE_GET_SUB_COMMENTS = get_sub_comment
    config.CRAWLER_MAX_NOTES_COUNT = crawler_max_notes_count

    crawler_type_var.set(type)
    asyncio.run(_run())


async def _init_db(db_type: str):
    from database.db import init_db as _init
    await _init(db_type)


async def _run():
    crawler = XiaoHongShuCrawler()
    await crawler.start()


if __name__ == "__main__":
    app()
