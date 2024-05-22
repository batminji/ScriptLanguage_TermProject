import requests
import xml.etree.ElementTree as ET
from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
from pyproj import Transformer
from googlemaps import Client
import io
import matplotlib.pyplot as plt

# 공공데이터 API 키
api_key = "4f72756e74646b6434354562524168"

# 서울시 구별 병원 정보 데이터
url = f"http://openapi.seoul.go.kr:8088/{api_key}/xml/LOCALDATA_051801/1/1000/"

response = requests.get(url)
root = ET.fromstring(response.content)
items = root.findall(".//row")

gu_code_to_name = {
    "3000000": "종로구",
    "3010000": "중구",
    "3020000": "용산구",
    "3030000": "성동구",
    "3040000": "광진구",
    "3050000": "동대문구",
    "3060000": "중랑구",
    "3070000": "성북구",
    "3080000": "강북구",
    "3090000": "도봉구",
    "3100000": "노원구",
    "3110000": "은평구",
    "3120000": "서대문구",
    "3130000": "마포구",
    "3140000": "양천구",
    "3150000": "강서구",
    "3160000": "구로구",
    "3170000": "금천구",
    "3180000": "영등포구",
    "3190000": "동작구",
    "3200000": "관악구",
    "3210000": "서초구",
    "3220000": "강남구",
    "3230000": "송파구",
    "3240000": "강동구",
}

hospitals = []
for item in items:
    gu_code = item.findtext("OPNSFTEAMCODE")
    gu_name = gu_code_to_name.get(gu_code)
    if gu_name:
        hospital = {
            "name": item.findtext("BPLCNM"),  # 이름
            "address": item.findtext("RDNWHLADDR"),  # 주소
            "lat": item.findtext("Y"),  # 중부원점Y
            "lng": item.findtext("X"),  # 중부원점X
            "gu": gu_name,  # 구 코드 -> 구 이름 변환
        }
        hospitals.append(hospital)

Google_API_Key = "AIzaSyAWB0-pa_0kD_HYrzuTFRBhPNn7Ln3YwSc"
gmaps = Client(key=Google_API_Key)

# EPSG:2097 중부원점TM 좌표계
epsg_2097 = 'epsg:2097'
# EPSG:4326 WGS84 좌표계
epsg_4326 = 'epsg:4326'
# Transformer 객체 생성
transformer = Transformer.from_crs(epsg_2097, epsg_4326)

# 구 코드 목록 생성
gu_list = sorted(set(hospital['gu'] for hospital in hospitals))

# tkinter GUI 생성
root = tk.Tk()
root.title("서울시 구별 미용업 정보")

# Notebook 생성
notebook = ttk.Notebook(root, width=800, height=600)
notebook.pack()

# 첫 번째 페이지 생성
frame1 = tk.Frame(root)
notebook.add(frame1, text="미용업 리스트")

# 구 선택 콤보박스 생성
selected_gu = tk.StringVar()
selected_gu.set(gu_list[0])  # 초기값 설정
gu_combo = ttk.Combobox(frame1, textvariable=selected_gu, values=gu_list)
gu_combo.pack()

# 지도 이미지 라벨 생성
map_label = tk.Label(frame1)
map_label.pack()

hospital_list = tk.Listbox(frame1, width=60)
hospital_list.pack(side=tk.LEFT, fill=tk.BOTH)

scrollbar = tk.Scrollbar(frame1)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

hospital_list.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=hospital_list.yview)


def show_hospitals():
    hospital_list.delete(0, tk.END)

    gu_name = selected_gu.get()
    hospitals_in_gu = [hospital for hospital in hospitals if hospital['gu'] == gu_name]

    for hospital in hospitals_in_gu:
        hospital_list.insert(tk.END, f"{hospital['name']} ({hospital['address']})")


def update_map():
    gu_name = selected_gu.get()
    gu_center = gmaps.geocode(f"서울특별시 {gu_name}")[0]['geometry']['location']
    gu_map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={gu_center['lat']},{gu_center['lng']}&zoom=14&size=400x400&maptype=roadmap"
    hospitals_in_gu = [hospital for hospital in hospitals if hospital['gu'] == gu_name]
    for hospital in hospitals_in_gu:
        if hospital['lat'] and hospital['lng']:
            x, y = float(hospital['lat']), float(hospital['lng'])
            lat, lng = transformer.transform(x, y)
            marker_url = f"&markers=color:red%7C{lat},{lng}"
            gu_map_url += marker_url

    # 지도 이미지 업데이트
    response = requests.get(gu_map_url + '&key=' + Google_API_Key)
    image = Image.open(io.BytesIO(response.content))
    photo = ImageTk.PhotoImage(image)
    map_label.configure(image=photo)
    map_label.image = photo

    show_hospitals()


def on_gu_select(event):
    pass


# 두 번째 페이지 생성
frame2 = tk.Frame(root)
notebook.add(frame2, text="구별 미용업 수")


# 그래프 생성 함수
def plot_bar_chart():
    gu_name = selected_gu.get()
    hospitals_in_gu = [hospital for hospital in hospitals if hospital['gu'] == gu_name]
    counts = {gu: 0 for gu in gu_list}
    for hospital in hospitals_in_gu:
        counts[hospital['gu']] += 1

    plt.figure(figsize=(10, 6))
    plt.bar(counts.keys(), counts.values(), color='skyblue')
    plt.xlabel('구')
    plt.ylabel('미용업 수')
    plt.title('서울시 구별 미용업 수')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# 그래프 버튼 생성
plot_button = tk.Button(frame2, text="그래프 보기", command=plot_bar_chart)
plot_button.pack()

# 세 번째 페이지 생성
frame3 = tk.Frame(root)
notebook.add(frame3, text="즐겨찾기 목록")

def send_email():
    # Gmail API 또는 smtplib를 사용하여 이메일 보내기 로직을 구현할 수 있습니다.
    # 여기에서는 실제 이메일 보내기 기능을 구현하기 보다는 간단하게 출력만 해보겠습니다.
    bookmark_list = ["미용업체1", "미용업체2", "미용업체3"]  # 임의의 즐겨찾기 목록
    print("Following bookmarked businesses will be sent via email:")
    for business in bookmark_list:
        print(business)

# 즐겨찾기 목록을 나타낼 리스트박스 생성
bookmark_listbox = tk.Listbox(frame3, width=60)
bookmark_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

# 즐겨찾기 목록을 나타내는 라벨 생성
bookmark_label = tk.Label(frame3, text="즐겨찾기 목록", font=("Helvetica", 16))
bookmark_label.pack()

# Gmail 보내기 버튼 생성
send_email_button = tk.Button(frame3, text="Gmail 보내기", command=send_email)
send_email_button.pack()

# 임의의 즐겨찾기 목록 추가
for business in ["미용업체1", "미용업체2", "미용업체3"]:
    bookmark_listbox.insert(tk.END, business)

gu_combo.bind("<<ComboboxSelected>>", on_gu_select)

update_map()

root.mainloop()


