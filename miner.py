import fitz
from PyPDF2 import PdfReader
from tkinter import PhotoImage


class PDFMiner:
    def __init__(self, file_path, window_height):
        self.file_path = file_path
        self.pdf = fitz.open(self.file_path)
        example_page = self.pdf.load_page(0)
        self.width, self.height = example_page.rect.width, example_page.rect.height

        self.pdf_reader = PdfReader(self.file_path)

        self.zoom_y = window_height / self.height
        self.zoom_x = ((self.zoom_y * self.height)/1.41) / self.width

    def get_metadata(self):
        metadata = self.pdf.metadata
        no_pages = self.pdf.page_count
        return metadata, no_pages

    def get_page(self, page_num):
        page = self.pdf.load_page(page_num)
        mat = fitz.Matrix(self.zoom_x, self.zoom_y)
        pix = page.get_pixmap(matrix=mat)
        px1 = fitz.Pixmap(pix, 0) if pix.alpha else pix
        imgdata = px1.tobytes("ppm")
        return PhotoImage(data=imgdata), px1.width

    def get_text(self, page_num):
        page = self.pdf_reader.pages[page_num]
        return page.extract_text()
