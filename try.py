import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import xml.etree.ElementTree as ET
import io
from googlemaps import Client
from pyproj import Transformer

class MainGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("미용~ 미용")

        # 캔버스 생성
        self.makeCanvas()
        original_image = Image.open("logo.png")  # 이미지 로드
        resized_image = original_image.resize((50, 50))
        img = ImageTk.PhotoImage(resized_image)
        self.canvas.create_image(50, 50, image=img, anchor="center")

        # 공공데이터 API 키
        self.api_key = "4f72756e74646b6434354562524168"
        self.Google_API_Key = "AIzaSyAWB0-pa_0kD_HYrzuTFRBhPNn7Ln3YwSc"

        # 구 코드 목록 생성
        self.gu_list = self.get_gu_list()

        # 구 선택 콤보박스 생성
        self.selected_gu = tk.StringVar()
        self.selected_gu.set(self.gu_list[0])  # 초기값 설정
        self.gu_combo = ttk.Combobox(self.root, textvariable=self.selected_gu, values=self.gu_list)
        self.canvas.create_window(300, 50, window=self.gu_combo)
        self.gu_combo.bind("<<ComboboxSelected>>", self.on_gu_select)

        # 지도 이미지 라벨 생성
        self.map_frame = tk.Frame(self.root)
        self.canvas.create_window(175, 300, width=300, height=300, window=self.map_frame)
        self.map_label = tk.Label(self.map_frame, width=200, height=300)
        self.map_label.pack(fill=tk.BOTH, expand=True)

        # 목록 리스트박스 생성
        self.list_frame = tk.Frame(self.root)
        self.canvas.create_window(300, 625, width=550, height=275, window=self.list_frame, anchor="center")
        self.salon_list = tk.Listbox(self.list_frame, width=60, height=30)
        self.salon_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 스크롤바 생성
        self.scrollbar = tk.Scrollbar(self.list_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.salon_list.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.salon_list.yview)

        # 초기 맵과 목록 업데이트
        self.update_map()
        self.showList()

        self.root.mainloop()

    def makeCanvas(self):
        self.canvas = tk.Canvas(self.root, bg='white', width=600, height=800)
        self.canvas.pack()

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
                    "name": item.findtext("BPLCNM"),  # 병원 이름
                    "address": item.findtext("RDNWHLADDR"),  # 병원 주소
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
            self.salon_list.insert(tk.END, f"{data['name']} ({data['address']})")

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

MainGUI()
