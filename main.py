import tkinter as tk
import tkinter.ttk
from PIL import Image, ImageTk

width = 600
height = 800

class MainGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("미용~ 미용")
        # 캔버스 생성
        self.canvas = tk.Canvas(self.root, bg='white', width=width, height=height)
        self.canvas.pack()

        # 로고 삽입
        original_image = Image.open("logo.png")  # 이미지 로드
        resized_image = original_image.resize((50, 50))
        img = ImageTk.PhotoImage(resized_image)
        self.canvas.create_image(50, 50, image=img, anchor="center")

        # 검색 프레임
        search_frame = tk.Frame(self.root)
        self.canvas.create_window(335, 50, width=500, height=50, window=search_frame, anchor="center")

        # 검색 입력 칸
        self.search_entry = tk.Entry(search_frame, width=60)
        self.search_entry.pack(side="left", padx=5)

        # 검색 버튼
        search_button = tk.Button(search_frame, text="검색", command=self.search)
        search_button.pack(side="left", padx=5)

        # 리스트 박스 프레임 생성
        list_frame = tk.Frame(self.root)
        self.canvas.create_window(300, 625, width=550, height=275, window=list_frame, anchor="center")

        # 리스트 박스 생성
        self.salon_list = tk.Listbox(list_frame, width=60, height=30)
        self.salon_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 스크롤 바 생성
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 스크롤 바 와 목록 연결
        self.salon_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.salon_list.yview)

        self.root.mainloop()

    def search(self):
        self.location = self.search_entry.get()



MainGUI()