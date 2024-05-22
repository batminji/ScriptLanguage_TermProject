import requests
import xml.etree.ElementTree as ET
from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
from pyproj import Transformer
from googlemaps import Client
import io
import matplotlib.pyplot as plt

class MainGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("서울시 구별 미용업 정보")

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
        self.map_label.pack()

        self.salon_list = tk.Listbox(self.frame1, width=60)
        self.salon_list.pack(side=tk.LEFT, fill=tk.BOTH)

        self.scrollbar = tk.Scrollbar(self.frame1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.salon_list.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.salon_list.yview)

        # 미용업체 정보 라벨 생성
        self.info_label = tk.Label(self.frame1, text="", justify=tk.LEFT)
        self.info_label.pack(side=tk.RIGHT, fill=tk.BOTH)

        # 그래프 버튼 생성
        self.plot_button = tk.Button(self.frame2, text="그래프 보기", command=self.plot_bar_chart)
        self.plot_button.pack()

        self.bookmark_listbox = tk.Listbox(self.frame3, width=60)
        self.bookmark_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        self.bookmark_label = tk.Label(self.frame3, text="즐겨찾기 목록", font=("Helvetica", 16))
        self.bookmark_label.pack()

        self.send_email_button = tk.Button(self.frame3, text="Gmail 보내기", command=self.send_email)
        self.send_email_button.pack()

        # 임의의 즐겨찾기 목록 추가
        for business in ["미용업체1", "미용업체2", "미용업체3"]:
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
                self.update_salon_map(salon_data)
                self.show_salon_info(salon_data)

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
        info_text = f"Name: {salon_data['name']}\nAddress: {salon_data['address']}\nLatitude: {salon_data['lat']}\nLongitude: {salon_data['lng']}"
        self.info_label.config(text=info_text)

    def plot_bar_chart(self):
        counts = {gu: 0 for gu in self.gu_list}
        for data in self.salons:
            counts[data['gu']] += 1

        plt.figure(figsize=(10, 6))
        plt.bar(counts.keys(), counts.values(), color='skyblue')
        plt.xlabel('구')
        plt.ylabel('미용업 수')
        plt.title('서울시 구별 미용업 수')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def send_email(self):
        # Gmail API 또는 smtplib를 사용하여 이메일 보내기 로직을 구현할 수 있습니다.
        # 여기에서는 실제 이메일 보내기 기능을 구현하기 보다는 간단하게 출력만 해보겠습니다.
        bookmark_list = ["미용업체1", "미용업체2", "미용업체3"]  # 임의의 즐겨찾기 목록
        print("Following bookmarked businesses will be sent via email:")
        for business in bookmark_list:
            print(business)

MainGUI()
