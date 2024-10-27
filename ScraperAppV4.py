import streamlit as st
import pandas as pd
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import urllib.parse
import time
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
import re
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googletrans import Translator
import random
import undetected_chromedriver as uc



############################################    VNEXPRESS    ############################################
#########################################################################################################
# Hàm tạo URL dựa trên từ khóa
def generate_url_with_keyword(keyword, page_number):
    base_url = "https://timkiem.vnexpress.net/"
    
    query_params = {
        'q': keyword,
        'media_type': 'text',
        'fromdate': '',
        'todate': '',
        'latest': 'on',
        'cate_code': '',
        'search_f': 'title,tag_list',
        'date_format': 'all',
        'page': page_number
    }
    
    query_string = urllib.parse.urlencode(query_params, doseq=True)
    full_url = f"{base_url}?{query_string}"
    
    return full_url

# Hàm lấy nội dung bài báo
def layscript(url):
    try:
        # Gửi request đến trang web
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra mã trạng thái HTTP
        response.encoding = 'utf-8'
    except requests.RequestException as e:
        # Nếu có lỗi trong quá trình gửi request
        return f"Không lấy được nội dung"

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p', class_='Normal')
        article_text = ' '.join([paragraph.get_text() for paragraph in paragraphs])
        
        sentences = re.split(r'(?<!\d)\.\s+', article_text.strip())
        if len(sentences) > 1:
            article_text = '. '.join(sentences[:-1])
        
        return article_text

    except Exception as e:
        # Nếu có lỗi trong quá trình phân tích HTML hoặc xử lý văn bản
        return f"Không lấy được nội dung"

# Hàm lấy ngày đăng bài báo
def laydate(url):
    try:
        # Gửi request đến trang web
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra mã trạng thái HTTP
        response.encoding = 'utf-8'
    except requests.RequestException as e:
        # Nếu có lỗi trong quá trình gửi request
        return "Không lấy được ngày đăng"

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        date = soup.find('span', class_='date')
        return date.get_text() if date else "Không rõ"

    except Exception as e:
        # Nếu có lỗi trong quá trình phân tích HTML hoặc lấy ngày
        return "Không lấy được ngày đăng"

# Hàm chính để cào bài báo theo từ khóa và số lượng bài báo
def vnexpress_theokeyword(keywords, sobaibao, progress_callback=None):
    page_number = 1
    data = []
    seen_titles = set()
    count = 0
    total_articles = sobaibao

    while count < sobaibao:
        url = generate_url_with_keyword(keywords, page_number)
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', class_='width_common list-news-subfolder')

        if container is None:
            break

        articles = container.find_all('a', href=True, title=True)
        new_articles_found = False

        for article in articles:
            if count >= sobaibao:
                break

            title = article.get('title')
            href = article.get('href')

            if title and href and title not in seen_titles:
                seen_titles.add(title)
                # Cập nhật đếm bài viết
                count += 1
                data.append([title, href])

                new_articles_found = True

        if not new_articles_found:
            break
        
        page_number += 1

    df = pd.DataFrame(data, columns=["Tiêu đề", "URL"])

    # Duyệt qua từng URL để lấy nội dung và ngày đăng
    for index, row in df.iterrows():
        df.at[index, 'Nội dung'] = layscript(row['URL'])
        df.at[index, 'Ngày đăng'] = laydate(row['URL'])

        # Cập nhật thanh tiến độ và hiển thị trạng thái
        if progress_callback:
            progress_callback(index + 1, total_articles)

    return df


############################################    CNBC    #################################################
#########################################################################################################

def cnbc_script(url):
    try:
        # Gửi request đến trang web
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra mã trạng thái HTTP
    except requests.RequestException as e:
        # Nếu có lỗi trong quá trình gửi request
        return f"Lỗi khi gửi request: {e}"

    try:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm element chứa nội dung bài báo dựa trên data-module
        article_container = soup.find('div', {'data-module': 'ArticleBody'})
        
        if article_container:
            # Tìm tất cả các đoạn văn trong element <p>
            paragraphs = article_container.find_all('p')
            if paragraphs:
                # Kết hợp nội dung các đoạn văn
                article_content = " ".join([p.get_text() for p in paragraphs])
                return article_content
        
        # Nếu không tìm thấy nội dung
        return "Không lấy được nội dung."
    
    except Exception as e:
        # Nếu có lỗi trong quá trình phân tích HTML hoặc lấy nội dung
        return "Không lấy được nội dung."


# Function to generate CNBC URL
def generate_cnbc_url_with_keywords(keywords):
    base_url = "https://www.cnbc.com/search/"
    query_params = {'query': keywords, 'qsearchterm': keywords}
    query_string = urllib.parse.urlencode(query_params)
    return f"{base_url}?{query_string}"


# Scrape CNBC news with progress callback
def scrape_cnbc_news(keywords, sobaibao, progress_callback=None):
    url = generate_cnbc_url_with_keywords(keywords)

    service = Service("C:/Users/Welcome/Documents/Python/Scrape tiktok video/chromedriver-win64/chromedriver.exe")
    options = Options()
    options.add_argument("disable-extensions")
    options.add_argument("headless")  # Nếu không cần giao diện trình duyệt
    options.add_argument("--mute-audio")
    
    browser = webdriver.Chrome(service=service, options=options)
    
    # Mở trang
    browser.get(url)
    print("CNBC search page loaded successfully")
    
    # Đợi trang tải hoàn tất
    time.sleep(22)  # Có thể tùy chỉnh thời gian này nếu trang tải chậm
    
    # Tìm đối tượng <select> và chọn giá trị "Articles"
    select_element = browser.find_element("id", "formatfilter")  # Tìm thẻ <select> theo id
    select_object = Select(select_element)  # Tạo đối tượng Select
    select_object.select_by_visible_text("Articles")  # Chọn tùy chọn "Articles"
    
    print("Selected 'Articles' from the dropdown")

    # Đợi một chút cho trang cập nhật kết quả tìm kiếm
    time.sleep(2)
    
    # Click vào đối tượng "newest" để sắp xếp theo ngày
    sort_element = browser.find_element("id", "sortdate")  # Tìm thẻ <div> theo id
    sort_element.click()  # Click vào thẻ
    print("Clicked on 'newest' to sort by date")

    # Đợi cho trang sắp xếp lại kết quả
    time.sleep(2)
    
    # Lấy phần tử chứa các bài báo
    search_container = browser.find_element("id", "searchcontainer")

    # Lưu trữ dữ liệu và URL đã thu thập để tránh trùng lặp
    data = []
    seen_urls = set()  # Tạo set để lưu trữ các URL duy nhất
    previous_article_count = 0  # Đếm số lượng bài báo trước khi cuộn

    while len(data) < sobaibao:
        # Lấy tất cả các bài báo trong search_container
        articles = search_container.find_elements("css selector", "div.SearchResult-searchResultContent")
        current_article_count = len(articles)  # Số lượng bài báo hiện tại

        if current_article_count == previous_article_count:
            print("No new articles loaded, stopping scroll.")
            break

        previous_article_count = current_article_count  # Cập nhật số lượng bài báo đã có

        for article in articles:
            if len(data) >= sobaibao:
                break
            
            # Lấy Tiêu đề và URL
            title_element = article.find_element("css selector", "div.SearchResult-searchResultTitle a.resultlink")
            title_text = title_element.text.strip()
            url = title_element.get_attribute("href")

            # Kiểm tra nếu URL đã tồn tại trong set seen_urls
            if url not in seen_urls:
                seen_urls.add(url)  # Thêm URL vào set để theo dõi

                # Lấy Label và Ngày đăng
                label_element = article.find_element("css selector", "div.SearchResult-searchResultEyebrow a")
                label_text = label_element.text.strip()
                date_element = article.find_element("css selector", "span.SearchResult-publishedDate")
                date_text = date_element.text.strip()

                # Kiểm tra nếu nhãn không chứa "PRO" hoặc "INVESTING CLUB"
                if "PRO" not in label_text and "CLUB" not in label_text:
                    data.append({
                        'Tiêu đề': title_text,
                        'URL': url,
                        'Ngày đăng': date_text
                    })

        # Cuộn xuống để tải thêm bài báo
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Scrolled down to load more articles")

        # Đợi để các bài báo mới được tải
        time.sleep(5)  # Điều chỉnh thời gian nếu cần

        # Cập nhật phần tử chứa các bài báo sau khi cuộn
        search_container = browser.find_element("id", "searchcontainer")

    # Đóng trình duyệt
    browser.quit()
    print("Browser closed successfully")
    
    # Tạo DataFrame từ dữ liệu
    df = pd.DataFrame(data)

    # Extract content with progress tracking
    if progress_callback:
        for idx in range(len(df)):
            df.loc[idx, 'Nội dung'] = cnbc_script(df.loc[idx, 'URL'])
            progress_callback(idx + 1, len(df))
    
    return df



############################################    VTV    ##################################################
#########################################################################################################

def vtv_script(url):
    try:
        # Gửi yêu cầu GET đến URL
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra mã trạng thái HTTP
    except requests.RequestException as e:
        # Nếu có lỗi trong quá trình gửi request
        return f"Không tìm thấy nội dung bài báo"

    try:
        # Tạo đối tượng BeautifulSoup để phân tích HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Cấu trúc HTML cũ: tìm thẻ <div> với thuộc tính data-field="body"
        content_div = soup.find('div', {'data-field': 'body', 'class': 'ta-justify', 'id': 'entry-body'})

        # Kiểm tra nếu không tìm thấy nội dung theo cấu trúc cũ
        if content_div is None:
            # Chuyển sang cấu trúc HTML mới: thẻ <div> với class="content_detail ta-justify" và id="entry-body"
            content_div = soup.find('div', {'class': 'content_detail ta-justify', 'id': 'entry-body'})
        
        # Nếu vẫn không tìm thấy, trả về thông báo
        if content_div is None:
            return "Không tìm thấy nội dung bài báo"

        # Tìm tất cả các thẻ <p> trong div đó
        paragraphs = content_div.find_all('p')

        # Bỏ đoạn văn cuối cùng nếu cần
        paragraphs = paragraphs[:-1]

        # Lấy nội dung từ mỗi thẻ <p> và kết hợp thành một chuỗi với khoảng trắng
        content = ' '.join([p.get_text() for p in paragraphs])

        # Trả về nội dung bài báo
        return content

    except Exception as e:
        # Nếu có lỗi trong quá trình phân tích HTML hoặc xử lý nội dung
        return f"Không tìm thấy nội dung bài báo"

def generate_vtv_url_with_keyword_and_page(keywords, page_number):
    base_url = "https://vtv.vn/tim-kiem.htm"
    
    # Tạo tham số truy vấn
    query_params = {
        'keywords': keywords,
        'page': page_number
    }
    
    # Tạo chuỗi query từ các tham số
    query_string = urllib.parse.urlencode(query_params)
    
    # Kết hợp base URL với chuỗi query
    full_url = f"{base_url}?{query_string}"
    
    return full_url

def scrape_vtv_news(keywords, limit, progress_callback=None):
    page_number = 1
    titles, urls, publish_dates = [], [], []
    
    while len(titles) < limit:
        url = generate_vtv_url_with_keyword_and_page(keywords, page_number)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles_list = soup.find('ul', id='SearchSolr1').find_all('li', class_='tlitem')
        if not articles_list:
            break
        for article in articles_list:
            if len(titles) >= limit:
                break
            title_tag = article.find('h4').find('a')
            title = title_tag['title']
            url = "https://vtv.vn" + title_tag['href']
            date = article.find('p', class_='time').text.strip()
            titles.append(title)
            urls.append(url)
            publish_dates.append(date)

        page_number += 1

    df = pd.DataFrame({'Tiêu đề': titles, 'URL': urls})
    
    # Extract content with progress tracking
    if progress_callback:
        for idx in range(len(df)):
            df.loc[idx, 'Nội dung'] = vtv_script(df.loc[idx, 'URL'])
            # Update progress with number of articles scraped and the original limit
            progress_callback(idx + 1, limit)
            
    df['Ngày đăng'] = publish_dates
    return df

############################################    CAFEF    ################################################
#########################################################################################################

def cafef_script(url):
    try:
        # Gửi yêu cầu GET đến URL
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra mã trạng thái HTTP
    except requests.RequestException as e:
        # Nếu có lỗi trong quá trình gửi request
        return f"Không tìm thấy nội dung"

    try:
        # Tạo đối tượng BeautifulSoup để phân tích HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ' '.join(p.get_text() for p in paragraphs)
        
        split_index = content.lower().find('địa chỉ')
        if split_index != -1:
            content = content[:split_index]
        
        content = re.sub(r'\s+', ' ', content).strip()
        
        pattern = r'\d{2}-\d{2}-\d{4} - \d{2}:\d{2} [APM]{2}'
        match = re.search(pattern, content)
        if match:
            start_index = match.end()
            return content[start_index:].strip()
        
        return content

    except Exception as e:
        # Nếu có lỗi trong quá trình phân tích HTML hoặc xử lý nội dung
        return f"Không tìm thấy nội dung"


def cafef_date(url):
    try:
        # Gửi yêu cầu GET đến URL
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra mã trạng thái HTTP
        response.encoding = 'utf-8'
    except requests.RequestException as e:
        # Nếu có lỗi trong quá trình gửi request
        return f"Lỗi khi gửi request: {e}"

    try:
        # Tạo đối tượng BeautifulSoup để phân tích HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        date = soup.find('span', class_='pdate')
        if date:
            raw_date = date.get_text().strip()
            return raw_date
        else:
            return "Không tìm thấy ngày đăng"

    except Exception as e:
        # Nếu có lỗi trong quá trình phân tích HTML hoặc lấy ngày
        return f"Không tìm thấy ngày đăng"

def generate_cafef_url_with_keyword_and_page(keyword, page_number):
    base_url = "https://cafef.vn/tim-kiem/"
    page_part = f"trang-{page_number}.chn"
    query_params = {'keywords': keyword}
    query_string = urllib.parse.urlencode(query_params)
    full_url = f"{base_url}{page_part}?{query_string}"
    return full_url

def cafef_theokeyword(keywords, sobaibao, progress_callback=None):
    page_number = 1
    total_articles = []
    total_urls = []
    
    while len(total_articles) < sobaibao:
        url = generate_cafef_url_with_keyword_and_page(keywords, page_number)
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('a', class_='box-category-link-title')
            if not articles:
                break
            titles = []
            urls = []
            for idx, article in enumerate(articles):
                title = article.get('title')
                link = article.get('href')
                full_link = f"https://cafef.vn{link}"
                titles.append(title)
                urls.append(full_link)
                total_articles.append(title)
                total_urls.append(full_link)
                if len(total_articles) >= sobaibao:
                    break
            page_number += 1
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            break
    
    if total_articles:
        df = pd.DataFrame({
            'Tiêu đề': total_articles[:sobaibao],
            'URL': total_urls[:sobaibao]
        })

        # Duyệt qua từng URL để lấy nội dung và ngày đăng
        for index, row in df.iterrows():
            df.at[index, 'Nội dung'] = cafef_script(row['URL'])
            df.at[index, 'Ngày đăng'] = cafef_date(row['URL'])

            # Cập nhật thanh tiến độ và hiển thị trạng thái
            if progress_callback:
                progress_callback(index + 1, sobaibao)  # Cập nhật tiến độ dựa trên số lượng URL đã xử lý


        return df
    else:
        return pd.DataFrame()
    

############################################    NGUOIQUANSAT    #########################################
#########################################################################################################

def ngquansat_script(url):
    try:
        # Gửi yêu cầu HTTP để lấy nội dung trang
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra nếu có lỗi HTTP
        
        # Phân tích nội dung HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Danh sách các cấu trúc cần kiểm tra
        structures_to_check = [
            {'tag': 'article', 'class': 'entry entry-no-padding'},  # Cấu trúc <article>
            {'tag': 'div', 'class': 'entry entry-no-padding'}  # Cấu trúc <div>
        ]
        
        # Tìm bài báo dựa trên cấu trúc trong danh sách
        article = None
        for structure in structures_to_check:
            article = soup.find(structure['tag'], class_=structure['class'])
            if article:
                break
        
        # Nếu không tìm thấy bài báo, trả về thông báo lỗi
        if not article:
            return "Không tìm thấy bài báo."
        
        # Tìm tất cả thẻ <p> bên trong thẻ chứa nội dung bài báo
        paragraphs = article.find_all('p')
        
        # Nối nội dung của các đoạn văn thành một chuỗi
        content = " ".join([p.get_text() for p in paragraphs])
        
        # Loại bỏ nội dung từ phần ">>" trở về sau nếu có
        index_of_marker = content.rfind(">>")
        if index_of_marker != -1:
            content = content[:index_of_marker].strip()  # Cắt chuỗi và loại bỏ khoảng trắng dư thừa
        
        return content
    
    except requests.exceptions.RequestException as e:
        return f"Không tìm thấy nội dung"
    except Exception as e:
        return f"Không tìm thấy nội dung"
    
def ngquansat_date(url):
    try:
        # Gửi yêu cầu HTTP để lấy nội dung của trang
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra mã trạng thái HTTP
        response.encoding = 'utf-8'  # Đảm bảo mã hóa đúng
    except requests.RequestException as e:
        # Nếu có lỗi trong quá trình gửi request
        return f"Không tìm thấy ngày đăng"

    try:
        # Phân tích cú pháp HTML bằng BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm thẻ <span> chứa ngày đăng bài
        date_span = soup.find('span', class_='sc-longform-header-date block-sc-publish-time')

        # Nếu không tìm thấy ngày đăng theo cấu trúc đầu tiên, kiểm tra cấu trúc thứ hai
        if not date_span:
            date_span = soup.find('span', class_='c-detail-head__time')

        # Nếu tìm thấy thẻ <span>, lấy nội dung ngày đăng
        if date_span:
            publish_date = date_span.get_text(strip=True)
            return publish_date
        else:
            return "Không tìm thấy ngày đăng"

    except Exception as e:
        # Nếu có lỗi trong quá trình phân tích HTML hoặc xử lý ngày đăng
        return f"Không tìm thấy ngày đăng"

def generate_nguoiquansat_url_with_keyword(keywords):
    base_url = "https://nguoiquansat.vn/search"
    
    # Tạo tham số truy vấn
    query_params = {
        'q': keywords
    }
    
    # Tạo chuỗi query từ các tham số
    query_string = urllib.parse.urlencode(query_params)
    
    # Kết hợp base URL với chuỗi query
    full_url = f"{base_url}?{query_string}"
    
    return full_url

def ngquansat_theo_keywords(keywords, sobaibao, progress_callback=None):
    # URL trang cần truy cập
    url = generate_nguoiquansat_url_with_keyword(keywords)

    # Khởi tạo trình duyệt
    service = Service("C:/Users/Welcome/Documents/Python/Scrape tiktok video/chromedriver-win64/chromedriver.exe")
    options = Options()
    options.add_argument("disable-extensions")
    options.add_argument("headless")  # Nếu không cần giao diện trình duyệt
    options.add_argument("--mute-audio")

    browser = webdriver.Chrome(service=service, options=options)
    print("Browser started successfully")

    # Mở trang
    browser.get(url)
    print("Nguoiquansat search page loaded successfully")
    time.sleep(5)
    
    # Danh sách chứa dữ liệu
    article_data = []

    # Số bài báo mỗi trang ban đầu và mỗi lần nhấn nút "Xem thêm"
    articles_per_page = 15
    additional_articles = 15

    # Tính số lần cần nhấn nút "Xem thêm" để đảm bảo thu thập đủ số bài báo
    total_pages_needed = (sobaibao - articles_per_page + additional_articles - 1) // additional_articles

    # Thu thập bài báo
    while len(article_data) < sobaibao and total_pages_needed >= 0:
        articles = browser.find_elements(By.CSS_SELECTOR, 'ul.onecms__loading li')
        for article in articles:
            try:
                title_element = article.find_element(By.CSS_SELECTOR, 'h3.b-grid__title a')
                title = title_element.text.strip()
                article_url = title_element.get_attribute('href')

                # Thêm bài báo vào danh sách mà không kiểm tra trùng lặp ngay
                article_data.append({'Tiêu đề': title, 'URL': article_url})

            except Exception as e:
                print(f"An error occurred: {e}")

        # Loại bỏ bài báo trùng lặp
        unique_articles = {article['URL']: article for article in article_data}.values()
        article_data = list(unique_articles)

        # Nếu số bài báo vẫn chưa đủ, tiếp tục nhấn nút "Xem thêm"
        if len(article_data) < sobaibao:
            try:
                # Cuộn xuống cuối trang để đảm bảo nút 'Xem thêm' có thể nhìn thấy
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Đợi một chút để trang tải thêm nội dung nếu cần

                # Cuộn đến nút 'Xem thêm'
                load_more_button = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.c-more-small.onecms__loadmore a'))
                )
                browser.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(1)  # Đợi một chút để nút được cuộn vào tầm nhìn

                # Sử dụng JavaScript để click nút nếu phương pháp click trực tiếp không hoạt động
                browser.execute_script("arguments[0].click();", load_more_button)
                time.sleep(5)  # Đợi để trang tải thêm bài viết mới
            except Exception as e:
                print(f"Could not find or click 'Load More' button: {e}")
                break

        total_pages_needed -= 1

    browser.quit()

    # Đảm bảo số lượng bài báo cuối cùng bằng số lượng yêu cầu
    final_articles = article_data[:sobaibao]

    # Tạo DataFrame từ dữ liệu đã thu thập
    df = pd.DataFrame(final_articles)

    # Duyệt qua từng URL để lấy nội dung và cập nhật tiến độ
    df['Nội dung'] = df['URL'].apply(lambda url: ngquansat_script(url))

    if progress_callback:
        for idx in range(len(df)):
            df.loc[idx, 'Ngày đăng'] = ngquansat_date(df.loc[idx, 'URL'])
            progress_callback(idx + 1, len(df))

    return df

############################################    VNECONOMY    ############################################
#########################################################################################################

def vneco_script(url):
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('div', class_='detail__content')

        if content_div is None:
            return "Không tìm thấy nội dung."

        paragraphs = content_div.find_all('p')
        article_content = ' '.join([p.get_text() for p in paragraphs])
        return article_content

    except requests.exceptions.RequestException as e:
        return f"Không tìm thấy nội dung"

    except Exception as e:
        return f"Không tìm thấy nội dung"

# Function to generate the search URL
def generate_vneconomy_url_with_keyword(keyword):
    base_url = "https://vneconomy.vn/tim-kiem.htm"
    query_params = {'q': keyword}
    query_string = urllib.parse.urlencode(query_params)
    full_url = f"{base_url}?{query_string}"
    return full_url

# Scraping function for VnEconomy
def vneco_theokeyword(keywords, sobaibao, progress_callback=None):
    url = generate_vneconomy_url_with_keyword(keywords)
    video_data = []

    # Selenium setup
    service = Service("C:/Users/Welcome/Documents/Python/Scrape tiktok video/chromedriver-win64/chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("disable-extensions")
    options.add_argument("headless")
    options.add_argument("--mute-audio")
    browser = webdriver.Chrome(service=service, options=options)

    browser.get(url)
    time.sleep(5)
    
    # Số bài báo trên trang và số bài báo mỗi lần nhấn nút "xem thêm"
    articles_per_page = 20
    additional_articles = 20
    
    # Tính số lần nhấn nút cần thiết
    total_pages_needed = (sobaibao - articles_per_page + additional_articles - 1) // additional_articles
    
    while len(video_data) < sobaibao and total_pages_needed >= 0:
        articles = browser.find_elements(By.CSS_SELECTOR, 'article.story.story--featured.story--timeline')
        if len(articles) == 0:
            break

        for article in articles:
            try:
                title_element = article.find_element(By.CSS_SELECTOR, 'h3.story__title a')
                title = title_element.text.strip()
                url = title_element.get_attribute('href')
                date_element = article.find_element(By.CSS_SELECTOR, 'div.story__meta time')
                date_posted = date_element.text.strip()
                
                # Thêm bài báo vào danh sách với cấu trúc cột chính xác từ đầu
                video_data.append({
                    'Tiêu đề': title,
                    'URL': url,
                    'Nội dung': '',  # Nội dung sẽ được cập nhật sau
                    'Ngày đăng': date_posted
                })

            except Exception as e:
                pass

        # Loại bỏ trùng lặp
        unique_articles = {article['URL']: article for article in video_data}.values()
        video_data = list(unique_articles)

        # Nếu số bài báo chưa đủ, nhấn nút "xem thêm" và giảm số lần nhấn nút cần thiết
        if len(video_data) < sobaibao:
            try:
                more_button = browser.find_element(By.CSS_SELECTOR, 'li.page-item.active a#moreResultSearch')
                browser.execute_script("arguments[0].scrollIntoView(true);", more_button)
                time.sleep(1)
                more_button.click()
                time.sleep(5)
            except Exception as e:
                break

        total_pages_needed -= 1

    browser.quit()

    # Đảm bảo số lượng bài báo cuối cùng bằng số lượng yêu cầu
    final_articles = video_data[:sobaibao]

    # Tạo DataFrame từ dữ liệu đã thu thập với thứ tự cột chính xác
    df = pd.DataFrame(final_articles, columns=['Tiêu đề', 'URL', 'Nội dung', 'Ngày đăng'])

    # Duyệt qua từng URL để lấy nội dung và cập nhật tiến độ
    for index, row in df.iterrows():
        df.at[index, 'Nội dung'] = vneco_script(row['URL'])

        # Cập nhật tiến độ sau khi xử lý mỗi URL
        if progress_callback:
            progress_callback(index + 1, sobaibao)

    return df



############################################    YOUTUBE    ##############################################
#########################################################################################################

def layscript_ytb(browser, url):
    print("Initiating scrape for youtube transcript")
    
    def extract_video_id(url):
        # Sử dụng regex để tìm video ID
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid YouTube URL")

    # Trích xuất video ID từ URL
    video_id = extract_video_id(url)

    # Danh sách các ngôn ngữ ưu tiên
    languages_priority = ['vi', 'en', 'fr', 'es']  # Thử tiếng Việt, Anh, Pháp, Tây Ban Nha

    transcript = None

    try:
        # Lấy danh sách tất cả các phụ đề có sẵn
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript_list in transcripts:
            language = transcript_list.language_code
            if language in languages_priority:
                transcript_list = transcript_list.fetch()
                transcript = ' '.join([item['text'] for item in transcript_list])
                print(f"Transcript found in language: {language}")
                break

        if not transcript:
            transcript = "video không tìm thấy script"
    except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound, Exception) as e:
        print(f"An error occurred: {e}")
        transcript = "video không tìm thấy script"
    
    # Loại bỏ "[âm nhạc]" khỏi transcript nếu tìm thấy
    transcript = transcript.replace("[âm nhạc]", "") if transcript else "video không tìm thấy script"
    transcript = transcript.replace("[vỗ tay]", "") if transcript else "video không tìm thấy script"
    
    return transcript


def generate_youtube_search_url_ytb(search_query):
    encoded_query = urllib.parse.quote(search_query)
    base_url = "https://www.youtube.com/results?search_query="
    sp_param = "&sp=CAMSBBABGAI%253D"
    full_url = f"{base_url}{encoded_query}{sp_param}"
    return full_url


def layscript_theo_keyword_ytb(search_query, so_video, progress_callback=None):
    url = generate_youtube_search_url_ytb(search_query)

    video_data = []

    # Khởi tạo trình duyệt
    service = Service("C:/Users/Welcome/Documents/Python/Scrape tiktok video/chromedriver-win64/chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_argument("disable-extensions")
    options.add_argument("headless")
    options.add_argument("--mute-audio")
    
    browser = webdriver.Chrome(service=service, options=options)
    print("Browser started successfully")

    # Mở trang youtube
    browser.get(url)
    print("Youtube search page loaded successfully")

    time.sleep(4)
    
    # Scroll trang xuống để tải thêm video
    last_height = browser.execute_script("return document.documentElement.scrollHeight")

    while len(browser.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')) < so_video:
        browser.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)  # Chờ một chút để trang tải thêm nội dung

        new_height = browser.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            print("No more content to load, stopping scroll.")
            break  # Nếu không có thêm nội dung mới thì dừng lại
        last_height = new_height

    # Lấy danh sách video sau khi cuộn trang
    videos = browser.find_elements(By.CSS_SELECTOR, 'ytd-video-renderer')[:so_video]

    # Tính tỷ lệ mỗi khi duyệt một video (0 đến 1)
    step = 1 / so_video if so_video > 0 else 1

    for index, video in enumerate(videos):
        title_element = video.find_element(By.CSS_SELECTOR, 'yt-formatted-string[aria-label]')
        title = title_element.text

        video_url_element = video.find_element(By.CSS_SELECTOR, 'a#thumbnail')
        video_url = video_url_element.get_attribute('href')

        metadata_elements = video.find_elements(By.CSS_SELECTOR, 'span.inline-metadata-item.style-scope.ytd-video-meta-block')
        
        if len(metadata_elements) >= 2:
            views = metadata_elements[0].text
            upload_date = metadata_elements[1].text
        else:
            views = 'N/A'
            upload_date = 'N/A'

        video_data.append({
            'Tiêu đề': title,
            'URL': video_url,
            'Ngày đăng': upload_date,
            'Lượt xem': views,
        })

        # Lấy transcript sau khi xử lý URL
        transcript = layscript_ytb(browser, video_url)
        video_data[index]['Nội dung'] = transcript

        # Gọi progress_callback để cập nhật thanh tiến độ sau mỗi lần duyệt xong một video
        if progress_callback:
            progress_callback(index + 1, so_video)

    # Tạo DataFrame
    df = pd.DataFrame(video_data, columns=['Tiêu đề', 'URL', 'Nội dung', 'Ngày đăng', 'Lượt xem'])

    # Đóng trình duyệt
    browser.quit()

    return df



############################################    TIKTOK    ###############################################
#########################################################################################################
def translate_to_vietnamese(text):
    # Tạo đối tượng Translator
    translator = Translator()

    try:
        # Dịch chuỗi từ tiếng Anh sang tiếng Việt
        translation = translator.translate(text, src='en', dest='vi')
        # Trả về văn bản đã dịch
        return translation.text
    except Exception as e:
        print(f"Translation error: {e}")
        return "Phần dịch script bị lỗi"


# Hàm để tạo độ trễ ngẫu nhiên giữa các thao tác
def random_sleep(min_seconds, max_seconds):
    time.sleep(random.uniform(min_seconds, max_seconds))

# Hàm cuộn trang
def scroll_page(driver):
    driver.execute_script("window.scrollBy(0, window.innerHeight);")
    random_sleep(1, 2)

def generate_tiktok_url_with_query(keywords):
    base_url = "https://www.tiktok.com/search"
    
    # Tạo tham số truy vấn
    query_params = {
        'q': keywords
    }
    
    # Tạo chuỗi query từ các tham số
    query_string = urllib.parse.urlencode(query_params)
    
    # Kết hợp base URL với chuỗi query
    full_url = f"{base_url}?{query_string}"
    
    return full_url


# Hàm để lấy transcript từ danh sách URL video
def tiktok_transcript_scraper_multiple(url_list):
    # URL trang cần truy cập
    url = 'https://script.tokaudit.io/'
    
    # Khởi tạo trình duyệt
    service = Service("C:/Users/Welcome/Documents/Python/Scrape tiktok video/chromedriver-win64/chromedriver.exe")
    options = Options()
    options.add_argument("disable-extensions")
    options.add_argument("headless")  # Nếu không cần giao diện trình duyệt
    options.add_argument("--mute-audio")
    
    # Mở trình duyệt
    browser = webdriver.Chrome(service=service, options=options)
    print("Browser started successfully")

    # Mở trang một lần
    browser.get(url)
    print("Tiktok scraper loaded successfully")
    time.sleep(9)

    transcripts = []  # Danh sách chứa các transcript

    # Lặp qua từng URL trong danh sách
    for input_url in url_list:
        try:
            # Tìm phần tử input và điền chuỗi vào
            input_element = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Enter Video Url"]'))
            )
            input_element.clear()  # Xóa nội dung input trước đó
            input_element.send_keys(input_url)
            print(f"URL {input_url} entered successfully")

            # Chờ một chút để đảm bảo thao tác nhập liệu hoàn tất
            time.sleep(1)

            # Tìm và click vào nút "START"
            start_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="START"]'))
            )
            start_button.click()
            print("Start button clicked successfully")
            
            # Chờ vài giây để phụ đề được tải sau khi bấm nút
            time.sleep(6)  # Điều chỉnh thời gian tùy thuộc vào tốc độ tải của trang

            # Tìm tất cả các phần tử chứa phụ đề
            subtitles_elements = browser.find_elements(By.CSS_SELECTOR, 'span.text.text-xs.text-justify')
            
            # Lấy nội dung từ từng phần tử và nối chúng lại thành chuỗi
            subtitles = " ".join([subtitle.text for subtitle in subtitles_elements])

            # Kiểm tra nếu có nội dung để dịch
            if subtitles.strip():
                transcripts.append(subtitles)  # Lưu phụ đề gốc
            else:
                print(f"No subtitles found for {input_url}")
                transcripts.append("No subtitles available")
        
        except Exception as e:
            print(f"Error processing URL {input_url}: {e}")
            transcripts.append("Error occurred")  # Ghi nhận lỗi nếu gặp phải

    # Đóng trình duyệt sau khi đã xử lý tất cả URL
    browser.quit()

    return transcripts


def scrape_tiktok_and_get_transcripts(keywords, max_videos, progress_callback=None):
    videos = []
    
    # Cài đặt ChromeOptions
    options = uc.ChromeOptions()
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("headless")  # Nếu không cần giao diện trình duyệt

    # Khởi tạo Chrome driver
    driver = uc.Chrome(options=options)

    search_url = generate_tiktok_url_with_query(keywords)
    # Mở trang tìm kiếm TikTok
    driver.get(search_url)

    # Số video hiện có
    no_new_videos_count = 0
    while len(videos) < max_videos * 2:  # Lấy gấp đôi số video cần thiết
        current_video_count = len(videos)
        scroll_page(driver)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        video_containers = soup.find_all('div', class_=re.compile(r'DivItemContainerForSearch'))
        
        for container in video_containers:
            if len(videos) >= max_videos * 2:
                break
            
            video_data = {}

            video_element = container.find('a', class_=re.compile(r'AVideoContainer'))
            if video_element:
                url = video_element['href']
                full_url = f"https://www.tiktok.com{url}" if url.startswith('/') else url
                video_data['url'] = full_url

            description_element = container.find('span', class_=re.compile(r'SpanText'))
            if description_element:
                full_description = description_element.get_text(separator=" ").strip()
                video_data['title'] = full_description  # Đổi tên cột thành 'Tiêu đề'

            date_element = container.find('div', class_=re.compile(r'DivTimeTag'))
            if date_element:
                date_posted = date_element.get_text().strip()
                video_data['date_posted'] = date_posted

            views_element = container.find('strong', class_=re.compile(r'StrongVideoCount'))
            if views_element:
                views_count = views_element.get_text().strip()
                video_data['views'] = views_count

            if ('url' in video_data and 'title' in video_data and 
                    'date_posted' in video_data and 'views' in video_data):
                # Kiểm tra xem video đã tồn tại trong danh sách hay chưa
                if video_data['url'] not in [video['url'] for video in videos]:
                    videos.append(video_data)

        if len(videos) == current_video_count:
            no_new_videos_count += 1
        else:
            no_new_videos_count = 0

        if len(videos) >= max_videos * 2 or no_new_videos_count >= 3:
            break
    
    driver.quit()
    
    # Tổng số bước để cào dữ liệu
    total_steps = len(videos) // 2  # Mỗi lần duyệt 2 URL sẽ cập nhật một lần
    step = 0

    transcripts = []

    for i in range(0, len(videos), 2):
        urls = [video['url'] for video in videos[i:i + 2]]  # Lấy 2 URL mỗi lần
        transcripts += tiktok_transcript_scraper_multiple(urls)  # Lấy nội dung video
        step += 1
        
        # Cập nhật thanh tiến độ
        if progress_callback:
            progress_callback(step, total_steps)

    df = pd.DataFrame(videos)
    df['Nội dung'] = transcripts

    # Dịch cột nội dung sang tiếng Việt
    df['Nội dung'] = df['Nội dung'].apply(translate_to_vietnamese)

    # Lọc ra các video có nội dung
    df_with_content = df[df['Nội dung'].str.strip() != '']

    # Nếu số video có nội dung ít hơn yêu cầu, giữ lại các video không có nội dung
    if len(df_with_content) < max_videos:
        df_with_content['views_numeric'] = df_with_content['views'].apply(
            lambda x: float(re.sub(r'[KM]', '', x)) * (1000 if 'K' in x else 1000000) if any(c in x for c in ['K', 'M']) else float(x)
        )
        needed_count = max_videos - len(df_with_content)
        
        # Lấy các video không có nội dung
        df_without_content = df[df['Nội dung'].str.strip() == '']
        df_without_content['views_numeric'] = df_without_content['views'].apply(
            lambda x: float(re.sub(r'[KM]', '', x)) * (1000 if 'K' in x else 1000000) if any(c in x for c in ['K', 'M']) else float(x)
        )
        
        # Kết hợp video có nội dung và video không có nội dung
        df_combined = pd.concat([df_with_content, df_without_content.nlargest(needed_count, 'views_numeric')])
        
        # Nếu tổng số video vẫn chưa đủ, sử dụng tất cả video không có nội dung
        if len(df_combined) < max_videos:
            df_combined = pd.concat([df_with_content, df_without_content])
        
        df_with_content = df_combined

    # Lọc và sắp xếp lại DataFrame theo lượt xem
    df_with_content['views_numeric'] = df_with_content['views'].apply(
        lambda x: float(re.sub(r'[KM]', '', x)) * (1000 if 'K' in x else 1000000) if any(c in x for c in ['K', 'M']) else float(x)
    )
    df_with_content = df_with_content.nlargest(max_videos, 'views_numeric')

    # Chọn cột và đổi tên cột theo yêu cầu
    df_final = df_with_content[['title', 'url', 'date_posted', 'Nội dung', 'views']]
    df_final.columns = ['Tiêu đề', 'URL', 'Ngày đăng', 'Nội dung', 'Lượt xem']
    
    return df_final.reset_index(drop=True)






############################################    MAIN APP    #############################################
#########################################################################################################
# Giao diện người dùng
def create_ui():
    st.title("NQN SCRAPER APP")

    keyword = st.text_input("Nhập từ khóa")
    sobaibao_video = st.number_input("Nhập số bài báo/video", min_value=1, max_value=2000, value=10)

    # Tạo hai cột cho các checkbox
    col1, col2 = st.columns(2)

    with col1:
        vtv_checked = st.checkbox("1/ ‏‏‎ ‎‏‏‎ ‎ VTV")
        vnexpress_checked = st.checkbox("2/ ‏‏‎ ‎‏‏‎ ‎  VnExpress")
        cafef_checked = st.checkbox("3/ ‏‏‎ ‎‏‏‎ ‎  Cafef")
        vneconomy_checked = st.checkbox("4/ ‏‏‎ ‎‏‏‎ ‎  VnEconomy")
        
    with col2:
        nguoiquansat_checked = st.checkbox("5/ ‏‏‎ ‎‏‏‎ ‎  Người Quan Sát")
        youtube_checked = st.checkbox("6/ ‏‏‎ ‎‏‏‎ ‎  YouTube")
        cnbc_checked = st.checkbox("7/ ‏‏‎ ‎‏‏‎ ‎  CNBC")
        tiktok_check = st.checkbox("8/ ‏‏‎ ‎‏‏‎ ‎  Tiktok (*)")
    if st.button("Chạy"):
        if keyword and sobaibao_video:
            start_time = time.time()
            run_scraping(
                keyword,
                sobaibao_video,
                vnexpress_checked,
                cafef_checked,
                nguoiquansat_checked,
                vneconomy_checked,
                vtv_checked,
                cnbc_checked,
                youtube_checked,
                tiktok_check
            )
            end_time = time.time()
            estimated_time = end_time - start_time
            st.success(f"Cào dữ liệu hoàn tất! Thời gian hoàn tất: {estimated_time:.2f} giây.")
        else:
            st.warning("Vui lòng nhập từ khóa và số bài báo/video.")


# Hàm chạy cào dữ liệu
def run_scraping(keyword, sobaibao_video, vnexpress, cafef, nguoiquansat, vneconomy, vtv, cnbc, youtube, tiktok):
    dfs = []  # Danh sách để lưu các DataFrame từ các nguồn
    progress_bars = {}  # Để theo dõi tiến độ cào dữ liệu
    include_views = youtube  # Kiểm tra nếu YouTube được chọn, sẽ thêm cột 'Lượt xem'
    
    # Cào dữ liệu từ VTV
    if vtv:
        progress_bars['vtv'] = st.progress(0, text="Đang cào dữ liệu từ VTV...")
        df_vtv = scrape_vtv_news(keyword, sobaibao_video, progress_callback=lambda current, total: update_progress(progress_bars['vtv'], current, total, "VTV"))
        df_vtv['Nguồn'] = 'VTV'
        if include_views:
            df_vtv['Lượt xem'] = None
        dfs.append(df_vtv)
        
    # Cào dữ liệu từ VnExpress
    if vnexpress:
        progress_bars['vnexpress'] = st.progress(0, text="Đang cào dữ liệu từ VnExpress...")
        df_vnexpress = vnexpress_theokeyword(keyword, sobaibao_video, progress_callback=lambda current, total: update_progress(progress_bars['vnexpress'], current, total, "VnExpress"))
        df_vnexpress['Nguồn'] = 'VnExpress'
        if include_views:
            df_vnexpress['Lượt xem'] = None  # Thêm cột 'Lượt xem' nếu có YouTube
        dfs.append(df_vnexpress)
    
    # Cào dữ liệu từ Cafef
    if cafef:
        progress_bars['cafef'] = st.progress(0, text="Đang cào dữ liệu từ Cafef...")
        df_cafef = cafef_theokeyword(keyword, sobaibao_video, progress_callback=lambda current, total: update_progress(progress_bars['cafef'], current, total, "Cafef"))
        df_cafef['Nguồn'] = 'Cafef'
        if include_views:
            df_cafef['Lượt xem'] = None
        dfs.append(df_cafef)

    # Cào dữ liệu từ VnEconomy
    if vneconomy:
        progress_bars['vneconomy'] = st.progress(0, text="Đang cào dữ liệu từ VnEconomy...")
        df_vneconomy = vneco_theokeyword(keyword, sobaibao_video, progress_callback=lambda current, total: update_progress(progress_bars['vneconomy'], current, total, "VnEconomy"))
        df_vneconomy['Nguồn'] = 'VnEconomy'
        if include_views:
            df_vneconomy['Lượt xem'] = None
        dfs.append(df_vneconomy)

    # Cào dữ liệu từ Người Quan Sát
    if nguoiquansat:
        progress_bars['nguoiquansat'] = st.progress(0, text="Đang cào dữ liệu từ Người Quan Sát...")
        df_nguoiquansat = ngquansat_theo_keywords(keyword, sobaibao_video, progress_callback=lambda current, total: update_progress(progress_bars['nguoiquansat'], current, total, "Người Quan Sát"))
        df_nguoiquansat['Nguồn'] = 'Người Quan Sát'
        if include_views:
            df_nguoiquansat['Lượt xem'] = None
        dfs.append(df_nguoiquansat)
    
    # Cào dữ liệu từ YouTube
    if youtube:
        progress_bars['youtube'] = st.progress(0, text="Đang cào dữ liệu từ YouTube...")
        df_youtube = layscript_theo_keyword_ytb(keyword, sobaibao_video, progress_callback=lambda current, total: update_progress(progress_bars['youtube'], current, total, "YouTube"))
        df_youtube['Nguồn'] = 'YouTube'
        # Giả sử hàm này trả về cả cột 'Lượt xem'
        dfs.append(df_youtube)
    
    # Cào dữ liệu từ CNBC
    if cnbc:
        progress_bars['cnbc'] = st.progress(0, text="Đang cào dữ liệu từ CNBC...")
        df_cnbc = scrape_cnbc_news(keyword, sobaibao_video, progress_callback=lambda current, total: update_progress(progress_bars['cnbc'], current, total, "CNBC"))
        df_cnbc['Nguồn'] = 'CNBC'
        if include_views:
            df_cnbc['Lượt xem'] = None
        dfs.append(df_cnbc)

    if tiktok:
        progress_bars['tiktok'] = st.progress(0, text="Đang cào dữ liệu từ Tiktok...")
        df_tiktok = scrape_tiktok_and_get_transcripts(keyword, sobaibao_video, progress_callback=lambda current, total: update_progress(progress_bars['tiktok'], current, total, "Tiktok"))
        df_tiktok['Nguồn'] = 'Tiktok'
        # Giả sử hàm này trả về cả cột 'Lượt xem'
        dfs.append(df_tiktok)
    
    # Gộp tất cả các DataFrame lại
    if dfs:
        final_df = pd.concat(dfs, ignore_index=True)
        st.success("Cào dữ liệu hoàn tất!")
        st.dataframe(final_df)
        
        # Tạo file Excel và cung cấp link tải về
        excel_filename = "articles.xlsx"
        final_df.to_excel(excel_filename, index=False)
        
        with open(excel_filename, "rb") as file:
            st.download_button(
                label="Tải về file Excel",
                data=file,
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("Chưa chọn trang báo nào để cào dữ liệu.")


# Cập nhật thanh tiến độ
def update_progress(progress_bar, current, total, source_name):
    progress = int((current / total) * 100)
    progress_bar.progress(progress, text=f"Đang cào dữ liệu từ {source_name}: ({current}/{total}) ")


if __name__ == "__main__":
    create_ui()