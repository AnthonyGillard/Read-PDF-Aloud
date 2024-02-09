import ctypes
import tkinter
import pyttsx3
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
import os
from miner import PDFMiner
import multiprocessing
import keyboard


def read_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


class PDFViewer:
    SCROLL_BAR_WIDTH = 16
    MENU_BAR_HEIGHT = 16
    AESTHETIC_PADDING = 16
    PAGE_WIDTH = 655

    def __init__(self, application):
        self.pdf_file_path = None
        self.file_is_open = None
        self.miner = None

        self.author = None
        self.name = None
        self.no_pages = None
        self.current_page = 0
        self.current_page_starting_from_one = 1

        self.page_image = None

        self.application = application
        self._get_full_screen_width_and_height()
        self._create_gui()

    def _get_full_screen_width_and_height(self):
        self.application_width = self.application.winfo_screenwidth()
        self.application_height = self.application.winfo_screenheight() - 48

        self.pdf_view_width = self.application_width / 2
        self.pdf_view_height = self.application_height * 0.9

        self.pdf_navigation_width = self.pdf_view_width
        self.pdf_navigation_height = self.application_height * 0.1

        self.text_view_width = self.application_width - self.pdf_view_width
        self.text_view_height = self.application_height

    def _create_gui(self):
        self._size_window_and_load_icon()
        self._create_menu_with_tabs()

        self._create_pdf_view()
        self._create_pdf_navigation_frame()
        self._create_text_view()
        self._create_text_reading_options_panel()
        self._create_keyboard_shortcuts()

    def _size_window_and_load_icon(self):
        self.application.title('PDF Viewer')
        self.application.resizable(width=0, height=0)
        self.application.state('zoomed')
        self.application.iconbitmap(self.application, 'images\\PDF Icon free.ico')

    def _create_menu_with_tabs(self):
        self.menu = Menu(self.application)
        self.application.config(menu=self.menu)
        self.file_tab = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_tab)
        self.file_tab.add_command(label="Open File", accelerator='o', command=self.open_file)
        self.file_tab.add_command(label="Exit", command=self.application.destroy)

    def _create_pdf_view(self):
        self.pdf_view = ttk.Frame(self.application, width=self.pdf_view_width, height=self.pdf_view_height)
        self.pdf_view.grid(row=0, column=0)
        self.pdf_view.grid_propagate(False)

        self.scroll_y = Scrollbar(self.pdf_view, orient=VERTICAL)
        self.scroll_y.grid(row=0, column=1, sticky='ns')
        self.scroll_x = Scrollbar(self.pdf_view, orient=HORIZONTAL)
        self.scroll_x.grid(row=1, column=0, sticky='we')

        self.canvas = Canvas(self.pdf_view, bg='#ECE8F3', width=self.pdf_view_width - self.SCROLL_BAR_WIDTH,
                             height=self.pdf_view_height - self.SCROLL_BAR_WIDTH)
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.canvas.grid(row=0, column=0)
        self.scroll_y.configure(command=self.canvas.yview)
        self.scroll_x.configure(command=self.canvas.xview)

    def _create_pdf_navigation_frame(self):
        self.pdf_navigation = ttk.Frame(self.application, width=self.pdf_navigation_width,
                                        height=self.pdf_navigation_height)
        self.pdf_navigation.grid(row=1, column=0)
        self.pdf_navigation.grid_propagate(False)

        self.up_arrow_icon = PhotoImage(file='images\\up_arrow.png')
        self.up_arrow = self.up_arrow_icon.subsample(20, 20)
        self.up_button = ttk.Button(self.pdf_navigation, image=self.up_arrow, command=self.previous_page)
        self.up_button.grid(row=0, column=1, padx=((self.pdf_navigation_width / 2) - self.up_arrow.width(), 5), pady=8)

        self.down_arrow_icon = PhotoImage(file='images\\down_arrow.png')
        self.down_arrow = self.down_arrow_icon.subsample(20, 20)
        self.down_button = ttk.Button(self.pdf_navigation, image=self.down_arrow, command=self.next_page)
        self.down_button.grid(row=0, column=3, pady=8)

        self.page_label = ttk.Label(self.pdf_navigation, text='page')
        self.page_label.grid(row=0, column=4, padx=5)

    def _create_text_view(self):
        self.text_view = ttk.Frame(width=(self.application_width/2)-(self.AESTHETIC_PADDING*2),
                                   height=self.pdf_view_height)
        self.text_view.propagate(False)
        self.text_box = tkinter.Text(self.text_view, font=("Times New Roman", 10), bg='#d3d3d3', fg='black',
                                     wrap=tkinter.WORD)
        self.text_box.config(height=1000, width=100)
        self.text_box.pack(side=TOP)
        self.text_view.place(x=self.pdf_view_width + self.AESTHETIC_PADDING, y=0)

    def _create_text_reading_options_panel(self):
        self.reading_options_panel = ttk.Frame(self.application, width=self.pdf_navigation_width,
                                        height=self.pdf_navigation_height)
        self.reading_options_panel.grid(row=1, column=1)
        self.reading_options_panel.grid_propagate(False)

        self.speaker = PhotoImage(file='images\\speaker.png')
        self.speaker = self.speaker.subsample(20, 20)
        self.speaker_button = ttk.Button(self.reading_options_panel, image=self.speaker, command=self.read_all_text)
        self.speaker_button.grid(row=0, column=1, padx=((self.pdf_navigation_width / 2) - self.up_arrow.width(), 5),
                                 pady=8)

    def _create_keyboard_shortcuts(self):
        self.application.bind('<o>', self.open_file)
        self.application.bind('<w>', self.previous_page)
        self.application.bind('<s>', self.next_page)
        self.application.bind('<r>', self.read_all_text)
        self.application.bind('<Control-r>', self.read_selected_text)

    def open_file(self, event=None):
        self.pdf_file_path = fd.askopenfilename(title='Select a PDF file', initialdir=os.getcwd(),
                                                filetypes=(('PDF', '*.pdf'), ))
        file_name = os.path.basename(self.pdf_file_path)

        self.miner = PDFMiner(self.pdf_file_path,
                              self.pdf_view_height - self.MENU_BAR_HEIGHT - (self.AESTHETIC_PADDING * 2))
        meta_data, no_pages = self.miner.get_metadata()

        self.current_page = 0
        self._store_meta_data(meta_data, no_pages, file_name)

        self.update_display()

    def _store_meta_data(self, meta_data, no_pages, file_name):
        self.name = meta_data.get('title', file_name[:-4])
        self.author = meta_data.get('author', None)
        self.no_pages = no_pages
        self.file_is_open = True
        self.application.title(self.name)

    def update_display(self):
        if 0 <= self.current_page < self.no_pages:
            self._display_page()
            self._display_text()

    def _display_page(self):
        self.page_image = self.miner.get_page(self.current_page)
        self.canvas.create_image((self.application_width / 2 - self.PAGE_WIDTH) / 2,
                                 self.AESTHETIC_PADDING, anchor='nw', image=self.page_image)
        self.current_page_starting_from_one = self.current_page + 1
        self.page_label['text'] = str(self.current_page_starting_from_one) + ' of ' + str(self.no_pages)

        region = self.canvas.bbox(ALL)
        self.canvas.configure(scrollregion=region)

    def _display_text(self):
        self.text = self.miner.get_text(self.current_page)
        self.text_box.delete(1.0, END)
        self.text_box.insert(tkinter.END, self.text)

    def next_page(self, event=None):
        if self.file_is_open:
            if self.current_page <= self.no_pages - 1:
                self.current_page += 1
                self.update_display()

    def previous_page(self, event=None):
        if self.file_is_open:
            if self.current_page > 0:
                self.current_page -= 1
                self.update_display()

    def read_all_text(self, event=None):
        self._run_read_aloud_process(self.text)

    def read_selected_text(self, event=None):
        sel_start, sel_end = self.text_box.tag_ranges("sel")

        if sel_start and sel_end:
            text = self.text_box.get(sel_start, sel_end)
            self._run_read_aloud_process(text)

    @staticmethod
    def _run_read_aloud_process(text):
        p = multiprocessing.Process(target=read_text, args=(text,))
        p.start()
        while p.is_alive():
            if keyboard.is_pressed('escape'):
                p.terminate()
            else:
                continue
        p.join()


if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

    root = Tk()
    app = PDFViewer(root)
    root.mainloop()
