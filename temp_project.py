import requests
import xml.etree.ElementTree as ET
from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
from pyproj import Transformer
from googlemaps import Client
import io
import matplotlib.pyplot as plt

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tkinter import simpledialog

class MainGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("미용~ 미용")

        # 이미지 로드
        self.off_star_image = Image.open("off_star.png")
        self.off_star_image = self.off_star_image.resize((50, 50))
        self.off_star_photo = ImageTk.PhotoImage(self.off_star_image)

        self.on_star_image = Image.open("on_star.png")
        self.on_star_image = self.on_star_image.resize((50, 50))
        self.on_star_photo = ImageTk.PhotoImage(self.on_star_image)

        self.direction_image = Image.open("map.png")
        self.direction_image = self.direction_image.resize((200, 200))
        self.direction_photo = ImageTk.PhotoImage(self.direction_image)

        # Notebook 생성
        self.notebook = ttk.Notebook(self.root, width=800, height=600)
        self.notebook.pack()

        # 첫 번째 페이지 생성
        self.frame1 = tk.Frame(self.root)
        self.notebook.add(self.frame1, text="미용업 리스트")

        # 두 번째 페이지 생성
        self.frame2 = tk.Frame(self.root)
        self.notebook.add(self.frame2, text="구별 미용업 수")

        # 세 번째 페이지 생성
        self.frame3 = tk.Frame(self.root)
        self.notebook.add(self.frame3, text="즐겨찾기 목록")

        self.api_key = "4f72756e74646b6434354562524168"
        self.Google_API_Key = "AIzaSyAWB0-pa_0kD_HYrzuTFRBhPNn7Ln3YwSc"

        self.gu_list = self.get_gu_list()

        self.selected_gu = tk.StringVar()
        self.selected_gu.set(self.gu_list[0])  # 초기값 설정
        self.gu_combo = ttk.Combobox(self.frame1, textvariable=self.selected_gu, values=self.gu_list)
        self.gu_combo.pack()

        self.map_label = tk.Label(self.frame1)
        self.map_label.pack(side=tk.TOP, anchor=tk.NW)

        self.info_label = tk.Text(self.frame1, wrap=tk.WORD, font=("돋움", 12), width=50, height=20)
        self.info_label.place(x=410, y=50)
        self.info_label.config(state=tk.DISABLED)

        # 길찾기 버튼 생성 (초기에는 숨김)
        self.directions_button = tk.Button(self.frame1, image=self.direction_photo, command=self.show_directions_map)
        self.directions_button.pack_forget()

        self.salon_list = tk.Listbox(self.frame1, width=70, font=("돋움", 12))
        self.salon_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.frame1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.salon_list.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.salon_list.yview)


        # 그래프 버튼 생성
        self.plot_button = tk.Button(self.frame2, text="그래프 보기", command=self.plot_bar_chart)
        self.plot_button.pack()

        self.bookmark_listbox = tk.Listbox(self.frame3, width=60)
        self.bookmark_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        self.bookmark_label = tk.Label(self.frame3, text="즐겨찾기 목록", font=("돋움", 16))
        self.bookmark_label.pack()

        self.send_email_button = tk.Button(self.frame3, text="Gmail 보내기", command=self.send_email)
        self.send_email_button.pack()

        # 즐겨찾기 목록 추가
        self.bookmarks = []
        for business in self.bookmarks:
            self.bookmark_listbox.insert(tk.END, business)

        self.gu_combo.bind("<<ComboboxSelected>>", self.on_gu_select)
        self.salon_list.bind("<<ListboxSelect>>", self.on_salon_select)

        self.update_map()

        self.root.mainloop()

    def get_gu_list(self):
        url = f"http://openapi.seoul.go.kr:8088/{self.api_key}/xml/LOCALDATA_051801/1/1000/"
        response = requests.get(url)
        root = ET.fromstring(response.content)
        items = root.findall(".//row")
        gu_code_to_name = {
            "3000000": "종로구", "3010000": "중구", "3020000": "용산구", "3030000": "성동구", "3040000": "광진구",
            "3050000": "동대문구", "3060000": "중랑구", "3070000": "성북구", "3080000": "강북구", "3090000": "도봉구",
            "3100000": "노원구", "3110000": "은평구", "3120000": "서대문구", "3130000": "마포구", "3140000": "양천구",
            "3150000": "강서구", "3160000": "구로구", "3170000": "금천구", "3180000": "영등포구", "3190000": "동작구",
            "3200000": "관악구", "3210000": "서초구", "3220000": "강남구", "3230000": "송파구", "3240000": "강동구",
        }
        self.salons = []
        for item in items:
            gu_code = item.findtext("OPNSFTEAMCODE")
            gu_name = gu_code_to_name.get(gu_code)
            if gu_name:
                data = {
                    "name": item.findtext("BPLCNM"),  # 미용업체 이름
                    "address": item.findtext("RDNWHLADDR"),  # 미용업체 주소
                    "lat": item.findtext("Y"),  # 중부원점Y
                    "lng": item.findtext("X"),  # 중부원점X
                    "gu": gu_name,  # 구 코드 -> 구 이름 변환
                    "type": item.findtext("UPTAENM")    # 업체 종류
                }
                self.salons.append(data)

        gu_list = sorted(set(gu_code_to_name.get(item.findtext("OPNSFTEAMCODE")) for item in items))
        return gu_list

    def showList(self):
        self.salon_list.delete(0, tk.END)
        gu_name = self.selected_gu.get()
        salons_in_gu = [data for data in self.salons if data['gu'] == gu_name]
        for data in salons_in_gu:
            self.salon_list.insert(tk.END, f"{data['name']}")

    def update_map(self):
        gu_name = self.selected_gu.get()
        gmaps = Client(key=self.Google_API_Key)
        gu_center = gmaps.geocode(f"서울특별시 {gu_name}")[0]['geometry']['location']
        gu_map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={gu_center['lat']},{gu_center['lng']}&zoom=14&size=400x400&maptype=roadmap"
        salons_in_gu = [data for data in self.salons if data['gu'] == gu_name]
        transformer = Transformer.from_crs('epsg:2097', 'epsg:4326')
        for data in salons_in_gu:
            if data['lat'] and data['lng']:
                x, y = float(data['lat']), float(data['lng'])
                lat, lng = transformer.transform(x, y)
                marker_url = f"&markers=color:red%7C{lat},{lng}"
                gu_map_url += marker_url
        response = requests.get(gu_map_url + '&key=' + self.Google_API_Key)
        image = Image.open(io.BytesIO(response.content))
        photo = ImageTk.PhotoImage(image)
        self.map_label.configure(image=photo)
        self.map_label.image = photo

    def on_gu_select(self, event):
        self.update_map()
        self.showList()

    def on_salon_select(self, event):
        selected_index = self.salon_list.curselection()
        if selected_index:
            selected_salon = self.salon_list.get(selected_index)
            salon_name = selected_salon.split(" (")[0]
            salon_data = next((salon for salon in self.salons if salon['name'] == salon_name), None)
            if salon_data:
                self.selected_salon_data = salon_data  # 선택된 미용업체 데이터를 저장
                self.update_salon_map(salon_data)
                self.show_salon_info(salon_data)
                self.directions_button.pack(side=tk.RIGHT, expand=True)

    def update_salon_map(self, salon_data):
        gmaps = Client(key=self.Google_API_Key)
        transformer = Transformer.from_crs('epsg:2097', 'epsg:4326')
        if salon_data['lat'] and salon_data['lng']:
            x, y = float(salon_data['lat']), float(salon_data['lng'])
            lat, lng = transformer.transform(x, y)
            salon_map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=16&size=400x400&maptype=roadmap"
            marker_url = f"&markers=color:red%7C{lat},{lng}"
            salon_map_url += marker_url
            response = requests.get(salon_map_url + '&key=' + self.Google_API_Key)
            image = Image.open(io.BytesIO(response.content))
            photo = ImageTk.PhotoImage(image)
            self.map_label.configure(image=photo)
            self.map_label.image = photo

    def show_salon_info(self, salon_data):
        gmaps = Client(key=self.Google_API_Key)
        place_result = gmaps.find_place(input=salon_data['name'], input_type='textquery', fields=['place_id'])
        if place_result['candidates']:
            place_id = place_result['candidates'][0]['place_id']
            place_details = gmaps.place(place_id=place_id, fields=['formatted_phone_number', 'opening_hours'])
            phone_number = place_details['result'].get('formatted_phone_number', 'N/A')
            opening_hours = "\n".join(place_details['result'].get('opening_hours', {}).get('weekday_text', []))
        else:
            phone_number = 'N/A'
            opening_hours = 'N/A'

        salon_data['phone_number'] = phone_number
        salon_data['opening_hours'] = opening_hours

        info_text = f"{salon_data['name']}\n업체 종류 : {salon_data['type']}\n위치 : {salon_data['address']}\n전화번호 : {phone_number}\n영업시간\n{opening_hours}"

        self.info_label.config(state=tk.NORMAL)  # 편집 가능 상태로 설정
        self.info_label.delete(1.0, tk.END)  # 기존 텍스트 삭제
        self.info_label.insert(tk.END, f"{salon_data['name']}\n", 'bold')
        self.info_label.insert(tk.END, f"업체 종류 : ", 'bold')
        self.info_label.insert(tk.END, f"{salon_data['type']}\n")
        self.info_label.insert(tk.END, f"위치 : ", 'bold')
        self.info_label.insert(tk.END, f"{salon_data['address']}\n")
        self.info_label.insert(tk.END, f"전화번호 : ", 'bold')
        self.info_label.insert(tk.END, f"{phone_number}\n")
        self.info_label.insert(tk.END, "\n영업시간\n", 'bold')
        self.info_label.insert(tk.END, f"{opening_hours}")
        self.info_label.config(state=tk.DISABLED)  # 다시 편집 불가 상태로 설정

        # 'bold' 태그를 굵은 글씨로 설정
        self.info_label.tag_configure('bold', font=("돋움", 12, "bold"))

    def plot_bar_chart(self):
        counts = {gu: 0 for gu in self.gu_list}
        for data in self.salons:
            counts[data['gu']] += 1

        max_salon_count = max(counts.values())

        # 캔버스 생성
        if hasattr(self, 'canvas'):
            self.canvas.destroy()
        self.canvas = tk.Canvas(self.frame2, width=800, height=600)
        self.canvas.pack()

        bar_width = 20
        x_gap = 30
        x0 = 60
        y0 = 400  # y0 값을 늘려서 막대그래프가 캔버스 안에 들어오도록 조정
        for i, gu in enumerate(self.gu_list):
            x1 = x0 + i * (bar_width + x_gap)
            y1 = y0 - 300 * counts[gu] / max_salon_count  # 막대의 높이를 조정
            self.canvas.create_rectangle(x1, y1, x1 + bar_width, y0, fill='blue')
            self.canvas.create_text(x1 + bar_width / 2 - 5, y0 + 10 + 5, text=gu, anchor='n', angle=45)
            self.canvas.create_text(x1 + bar_width / 2 - 5, y1 - 10 + 5, text=counts[gu], anchor='s')

    def show_directions_map(self):
        salon_data = self.selected_salon_data  # 저장된 선택된 미용업체 데이터 사용
        gmaps = Client(key=self.Google_API_Key)
        transformer = Transformer.from_crs('epsg:2097', 'epsg:4326')

        # 한국공대 위도경도
        tuk_lat, tuk_lng = 37.2840, 127.0436

        if salon_data['lat'] and salon_data['lng']:
            x, y = float(salon_data['lat']), float(salon_data['lng'])
            lat, lng = transformer.transform(x, y)

            directions_result = gmaps.directions(
                (tuk_lat, tuk_lng),
                (lat, lng),
                mode="driving"
            )

            polyline = directions_result[0]['overview_polyline']['points']
            print(f"Polyline: {polyline}")

            path_url = f"&path=enc:{polyline}"
            directions_map_url = f"https://maps.googleapis.com/maps/api/staticmap?size=600x400&maptype=roadmap"
            marker_url = f"&markers=color:blue%7C{tuk_lat},{tuk_lng}&markers=color:red%7C{salon_lat},{salon_lng}"
            full_url = directions_map_url + marker_url + path_url + '&key=' + self.Google_API_Key

            response = requests.get(full_url)
            image = Image.open(io.BytesIO(response.content))
            photo = ImageTk.PhotoImage(image)

            # 기존 내용을 모두 제거
            for widget in self.frame1.winfo_children():
                widget.pack_forget()
            self.info_label.place_forget()

            # 새 지도 표시
            self.map_label = tk.Label(self.frame1, image=photo)
            self.map_label.image = photo  # 이미지가 가비지 컬렉션되지 않도록 참조 유지
            self.map_label.pack()

            # 뒤로가기 버튼 생성
            self.back_button = tk.Button(self.frame1, text="뒤로가기", command=self.go_back)
            self.back_button.pack(side=tk.LEFT, padx=10, pady=10)

            # 즐겨찾기 버튼 생성
            self.bookmark_button = tk.Button(self.frame1, image=self.off_star_photo, command=self.toggle_bookmark)
            self.bookmark_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def toggle_bookmark(self):
        # 버튼 이미지 토글
        current_image = self.bookmark_button.cget('image')
        if current_image == str(self.off_star_photo):
            self.bookmark_button.config(image=self.on_star_photo)
            self.add_to_bookmarks()
        else:
            self.bookmark_button.config(image=self.off_star_photo)
            self.remove_from_bookmarks()

    def go_back(self):
        # 첫 번째 페이지의 위젯을 다시 표시
        for widget in self.frame1.winfo_children():
            widget.pack_forget()

        self.gu_combo.pack()
        self.map_label.pack(side=tk.TOP, anchor=tk.NW)
        self.salon_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_label.place(x=400, y=50)
        self.directions_button.pack(side=tk.RIGHT, expand=True)

    def add_to_bookmarks(self):
        # 선택된 미용업체를 즐겨찾기 목록에 추가
        salon_data = self.selected_salon_data
        if salon_data['name'] not in self.bookmarks:
            self.bookmarks.append(salon_data['name'])
            self.bookmark_listbox.insert(tk.END, salon_data['name'])

    def remove_from_bookmarks(self):
        # 선택된 미용업체를 즐겨찾기 목록에서 제거
        salon_data = self.selected_salon_data
        if salon_data['name'] in self.bookmarks:
            self.bookmarks.remove(salon_data['name'])
            idx = self.bookmark_listbox.get(0, tk.END).index(salon_data['name'])
            self.bookmark_listbox.delete(idx)

    def send_email(self):
        recipient_email = simpledialog.askstring("Gmail 보내기", "enter gmail")

        # 즐겨찾기 목록 텍스트 준비
        bookmark_text = ""
        for bookmark in self.bookmarks:
            salon_info = next((salon for salon in self.salons if salon['name'] == bookmark), None)
            if salon_info:
                bookmark_text += (
                    f"이름: {salon_info['name']}\n"
                    f"업체 종류: {salon_info['type']}\n"
                    f"위치: {salon_info['address']}\n"
                    f"전화번호: {salon_info.get('phone_number', 'N/A')}\n"
                    f"영업시간: {salon_info.get('opening_hours', 'N/A')}\n"
                    "-----------------------------\n"
                )
        if not bookmark_text:
            bookmark_text = "즐겨찾기 목록이 비어 있습니다."

        sender_email = "dkdus78655@gmail.com"
        sender_password = "nexw okos qukc cvev"

        # 이메일 내용 구성
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "즐겨찾기 목록"
        body = f"즐겨찾기 목록:\n\n{bookmark_text}"
        msg.attach(MIMEText(body, 'plain'))

        try:
            # Gmail SMTP 서버에 연결하여 이메일 전송
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            tk.messagebox.showinfo("성공", "이메일이 성공적으로 전송되었습니다.")
        except Exception as e:
            tk.messagebox.showerror("오류", f"이메일 전송 중 오류가 발생했습니다.\n{str(e)}")

MainGUI()
