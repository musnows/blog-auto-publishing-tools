import sys

import pyperclip
from selenium.webdriver import Keys, ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select

from publisher.common_handler import wait_login
from utils.file_utils import read_file_with_footer, parse_front_matter, download_image
from utils.yaml_file_utils import read_jianshu, read_common, read_segmentfault, read_oschina, read_zhihu, read_51cto, \
    read_infoq, read_txcloud, read_csdn
import time


def csdn_publisher(driver, content=None):
    csdn_config = read_csdn()
    common_config = read_common()
    if content:
        common_config['content'] = content
    # print("content is :", common_config['content'])
    auto_publish = common_config['auto_publish']
    # 提取markdown文档的front matter内容：
    front_matter = parse_front_matter(common_config['content'])
    # print("front_matter is :", front_matter)

    # 打开新标签页并切换到新标签页
    driver.switch_to.new_window('tab')

    # 浏览器实例现在可以被重用，进行你的自动化操作
    driver.get(csdn_config['site'])
    time.sleep(2)  # 等待2秒


    # 文章标题
    wait_login(driver, By.XPATH, '//div[contains(@class,"article-bar")]//input[contains(@placeholder,"请输入文章标题")]')
    title = driver.find_element(By.XPATH, '//div[contains(@class,"article-bar")]//input[contains(@placeholder,"请输入文章标题")]')
    title.clear()
    if 'title' in front_matter and front_matter['title']:
        title.send_keys(front_matter['title'])
    else:
        title.send_keys(common_config['title'])
    time.sleep(2)  # 等待3秒

    # 文章内容 markdown版本
    file_content = read_file_with_footer(common_config['content'])
    # 如果文章中有特殊格式，替换
    file_content = file_content.replace("{abbrlink}", str(front_matter.get("abbrlink")))
    file_content = file_content.replace("{title}", str(front_matter.get("title")))
    file_content = file_content.replace("{date}", str(front_matter.get("date")))

    # 用的是CodeMirror,不能用元素赋值的方法，所以我们使用拷贝的方法
    cmd_ctrl = Keys.COMMAND if sys.platform == 'darwin' else Keys.CONTROL
    # 将要粘贴的文本内容复制到剪贴板
    pyperclip.copy(file_content)
    action_chains = webdriver.ActionChains(driver)
    content = driver.find_element(By.XPATH, '//div[@class="editor"]//div[@class="cledit-section"]')
    content.click()
    time.sleep(2)
    # 模拟实际的粘贴操作
    action_chains.key_down(cmd_ctrl).send_keys('v').key_up(cmd_ctrl).perform()
    time.sleep(3)  # 等待3秒

    # 右上角发布文章按钮
    send_button = driver.find_element(By.XPATH, '//button[contains(@class, "btn-publish") and contains(text(),"发布文章")]')
    send_button.click()
    time.sleep(2)

    # 文章标签
    if 'tags' in front_matter and front_matter['tags']:
        tags = front_matter['tags']
    else:
        tags = csdn_config['tags']
    if tags:
        add_tag = driver.find_element(By.XPATH,
                                        '//div[@class="mark_selection"]//button[@class="tag__btn-tag" and contains(text(),"添加文章标签")]')
        add_tag.click()
        time.sleep(1)
        tag_input = driver.find_element(By.XPATH, '//div[@class="mark_selection_box"]//input[contains(@placeholder,"请输入文字搜索")]')
        for tag in tags:
            tag_input.send_keys(tag)
            time.sleep(2)
            tag_input.send_keys(Keys.ENTER)
            time.sleep(1)

        # 关闭按钮
        close_button = driver.find_element(By.XPATH, '//div[@class="mark_selection_box"]//button[@title="关闭"]')
        close_button.click()
        time.sleep(1)

    # 文章封面
    cover_image = front_matter.get('image') or front_matter.get('cover')
    if cover_image != "":
        file_input = driver.find_element(By.XPATH, "//input[@class='el-upload__input' and @type='file']")
        # 文件上传不支持远程文件上传，所以需要把图片下载到本地
        file_input.send_keys(download_image(front_matter['image']))
        time.sleep(2)

    # 摘要
    if 'description' in front_matter and front_matter['description']:
        summary = front_matter['description']
    else:
        summary = common_config['summary']
    if summary:
        summary_input = driver.find_element(By.XPATH, '//div[@class="desc-box"]//textarea[contains(@placeholder,"摘要：会在推荐、列表等场景外露")]')
        summary_input.send_keys(summary)
        time.sleep(2)

    # 分类专栏
    categories = csdn_config['categories'] if not front_matter.get('categories') else front_matter['categories']
    if categories:
        # 先点击新建分类专栏
        add_category = driver.find_element(By.XPATH, '//div[@id="tagList"]//button[@class="tag__btn-tag" and contains(text(),"新建分类专栏")]')
        add_category.click()
        time.sleep(1)
        for category in categories:
            # 设置专栏分类的映射（md文件和csdn的映射）
            categories_tables = csdn_config.get('categories_tables')
            if categories_tables:
                category_name = ','.join(category) if isinstance(category, list) else category
                # 专栏名字优先使用映射后的，如果没有则直接用拼接出来的或者原名
                category = categories_tables.get(category_name, category_name)
            # 设置专栏
            category_input = driver.find_element(By.XPATH, f'//input[@type="checkbox" and @value="{category}"]/..')
            category_input.click()
            time.sleep(1)
        # 点击关闭按钮
        close_button = driver.find_element(By.XPATH, '//div[@class="tag__options-content"]//button[@class="modal__close-button button" and @title="关闭"]')
        close_button.click()
        time.sleep(1)

    # 可见范围
    visibility = csdn_config['visibility']
    if visibility:
        visibility_input = driver.find_element(By.XPATH,f'//div[@class="switch-box"]//label[contains(text(),"{visibility}")]')
        parent_element = visibility_input.find_element(By.XPATH, '..')
        parent_element.click()

    # 发布
    if auto_publish:
        publish_button = driver.find_element(By.XPATH, '//div[@class="modal__button-bar"]//button[contains(text(),"发布文章")]')
        publish_button.click()
        time.sleep(2) # 等待文章发布成功
        link_element = driver.find_element(By.XPATH, '//a[contains(text(),"查看文章")]')
        article_url = link_element.get_attribute("href")
        print("CSDN文章链接：", article_url)

    # 无论如何都等待2秒，避免后续操作和当前页面冲突
    time.sleep(2)
