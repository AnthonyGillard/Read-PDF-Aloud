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


class CONSTANTS:
    SCROLL_BAR_WIDTH = 16
    MENU_BAR_HEIGHT = 16
    AESTHETIC_PADDING = 16
    GUI_X_POSITION = 20
    GUI_Y_POSITION = 20
    GUI_WIDTH = 1850
    GUI_HEIGHT = 925


class Application:
    CONSTANTS = CONSTANTS()

    def __init__(self, application):
        self.file_is_open = False
        self.metadata_miner = None

        self.author = None
        self.name = None
        self.no_pages = None
        self.current_page = 0
        self.current_page_starting_from_one = 1
        self.page_text = ""

        self.page_image = None

        self.application = application
        self._calculate_frame_heights_and_widths()
        self._create_gui()

    def _calculate_frame_heights_and_widths(self):
        self.application_width = self.CONSTANTS.GUI_WIDTH
        self.application_height = self.CONSTANTS.GUI_HEIGHT

        self.pdf_view_width = self.application_width / 2
        self.pdf_view_height = self.application_height * 0.94

        self.pdf_navigation_width = self.pdf_view_width
        self.pdf_navigation_height = self.application_height * 0.1

        self.text_view_width = self.application_width - self.pdf_view_width
        self.text_view_height = self.application_height

    def _create_gui(self):
        self.pdf_display = PDFDisplay(self.application, self.pdf_view_width, self.pdf_view_height)
        self.pdf_navigation = PDFNavigation(self.application, self.go_to_previous_page, self.go_to_next_page,
                                            self.pdf_navigation_width, self.pdf_navigation_height)
        self.text_display = TextDisplay(self.application, self.pdf_view_width, self.pdf_view_height)
        self.text_navigation = TextNavigation(self.application, self.text_display.read_all_text,
                                              self.pdf_navigation_width, self.pdf_navigation_height)

        self.metadata_miner = None

        self._size_window_and_load_icon()
        self._create_menu_with_tabs()
        self._create_keyboard_shortcuts()

    def _size_window_and_load_icon(self):
        self.application.title('PDF Viewer')
        self.application.resizable(width=0, height=0)
        self.application.geometry(
            f'{self.application_width}x{self.application_height}+{self.CONSTANTS.GUI_X_POSITION}+'
            f'{self.CONSTANTS.GUI_Y_POSITION}')
        self.application.iconbitmap(self.application, 'images\\PDF Icon free.ico')

    def _create_menu_with_tabs(self):
        self.menu = Menu(self.application)
        self.application.config(menu=self.menu)

        self.file_tab = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_tab)
        self.file_tab.add_command(label="Open File", accelerator='o', command=self.open_file)
        self.file_tab.add_command(label="Exit", command=self.application.destroy)

        self.pdf_view_settings_tab = Menu(self.menu)

        self.text_settings_tab = Menu(self.menu)
        self.menu.add_cascade(label="Text Viewer Settings", menu=self.text_settings_tab)
        self.text_settings_tab.add_command(label="font size")

    def _create_keyboard_shortcuts(self):
        self.application.bind('<o>', self.open_file)
        self.application.bind('<w>', self.go_to_previous_page)
        self.application.bind('<s>', self.go_to_next_page)
        self.application.bind('<r>', self.text_display.read_all_text)
        self.application.bind('<Control-r>', self.text_display.read_selected_text)

    def open_file(self, event=None):
        file_path = fd.askopenfilename(title='Select a PDF file', initialdir=os.getcwd(),
                                       filetypes=(('PDF', '*.pdf'), ))
        file_name = os.path.basename(file_path)

        self.metadata_miner = PDFMiner(file_path, self.pdf_view_height - self.CONSTANTS.MENU_BAR_HEIGHT -
                                       (self.CONSTANTS.AESTHETIC_PADDING * 2))
        meta_data, no_pages = self.metadata_miner.get_metadata()

        self.current_page = 0
        self._store_meta_data(meta_data, no_pages, file_name)

        self.file_is_open = True

        page_image, page_image_width = self.metadata_miner.get_page(self.current_page)
        self.pdf_display.display_page(page_image, page_image_width)

    def update_display(self):
        if 0 <= self.current_page < self.no_pages:
            page_image, page_image_width = self.metadata_miner.get_page(self.current_page)
            self.pdf_display.display_page(page_image, page_image_width)
            self.pdf_navigation.update_current_page_graphic(self.current_page, self.no_pages)
            self.page_text = self.metadata_miner.get_text(self.current_page)
            self.text_display.display_text(self.page_text)

    def _store_meta_data(self, meta_data, no_pages, file_name):
        self.name = meta_data.get('title', file_name[:-4])
        self.author = meta_data.get('author', None)
        self.no_pages = no_pages
        self.application.title(self.name)

    def go_to_previous_page(self, event=None):
        if self.file_is_open and self.current_page > 0:
            self.current_page -= 1
            self.update_display()

    def go_to_next_page(self, event=None):
        if self.file_is_open and self.current_page < self.no_pages:
            self.current_page += 1
            self.update_display()


class PDFDisplay:
    CONSTANTS = CONSTANTS()

    def __init__(self, application, width, height):
        self.application = application
        self.width = width
        self.height = height

        self.current_page = 0
        self.current_page_starting_from_one = 1
        self.metadata_miner = None
        self.page_image = None

        self._create_frame()

    def get_current_page(self):
        return self.current_page_starting_from_one

    def _create_frame(self):
        self.frame = ttk.Frame(self.application, width=self.width, height=self.height)
        self.frame.grid(row=0, column=0)
        self.frame.grid_propagate(False)

        self.scroll_y = Scrollbar(self.frame, orient=VERTICAL)
        self.scroll_y.grid(row=0, column=1, sticky='ns')
        self.scroll_x = Scrollbar(self.frame, orient=HORIZONTAL)
        self.scroll_x.grid(row=1, column=0, sticky='we')

        self.canvas = Canvas(self.frame, bg='#ECE8F3', width=self.width - self.CONSTANTS.SCROLL_BAR_WIDTH,
                             height=self.width - self.CONSTANTS.SCROLL_BAR_WIDTH)
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.canvas.grid(row=0, column=0)
        self.scroll_y.configure(command=self.canvas.yview)
        self.scroll_x.configure(command=self.canvas.xview)

    def display_page(self, page_image, page_image_width):
        self.page_image = page_image
        self.canvas.create_image((self.width - page_image_width) / 2,
                                 self.CONSTANTS.AESTHETIC_PADDING, anchor='nw', image=self.page_image)

        region = self.canvas.bbox(ALL)
        self.canvas.configure(scrollregion=region)


class PDFNavigation:
    CONSTANTS = CONSTANTS()

    def __init__(self, application, go_to_previous_page_handle, go_to_next_page_handle, width, height):
        self.application = application
        self.width = width
        self.height = height

        self._create_frame(go_to_previous_page_handle, go_to_next_page_handle)

    def _create_frame(self, go_to_previous_page_handle, go_to_next_page_handle):
        self.frame = ttk.Frame(self.application, width=self.width,
                               height=self.height)
        self.frame.grid(row=1, column=0)
        self.frame.grid_propagate(False)

        self.up_arrow_icon = PhotoImage(file='images\\up_arrow.png')
        self.up_arrow = self.up_arrow_icon.subsample(20, 20)
        self.up_button = ttk.Button(self.frame, image=self.up_arrow, command=go_to_previous_page_handle)
        self.up_button.grid(row=0, column=1, padx=((self.width / 2) - self.up_arrow.width(), 5), pady=8)

        self.down_arrow_icon = PhotoImage(file='images\\down_arrow.png')
        self.down_arrow = self.down_arrow_icon.subsample(20, 20)
        self.down_button = ttk.Button(self.frame, image=self.down_arrow, command=go_to_next_page_handle)
        self.down_button.grid(row=0, column=3, pady=8)

        self.page_label = ttk.Label(self.frame, text='page')
        self.page_label.grid(row=0, column=4, padx=5)

    def update_current_page_graphic(self, current_page, total_pages):
        self.page_label['text'] = str(current_page) + ' of ' + str(total_pages)


class TextDisplay:
    CONSTANTS = CONSTANTS()

    def __init__(self, application, width, height):
        self.application = application
        self.width = width
        self.height = height

        self._create_text_view()

    def _create_text_view(self):
        self.text_view = ttk.Frame(width=self.width-self.CONSTANTS.AESTHETIC_PADDING*2, height=self.height)
        self.text_view.propagate(False)
        self.text_box = tkinter.Text(self.text_view, font=("Times New Roman", 8), bg='#d3d3d3', fg='black',
                                     wrap=tkinter.WORD)
        self.text_box.config(height=1000, width=100)
        self.text_box.pack(side=TOP)
        self.text_view.place(x=self.width + self.CONSTANTS.AESTHETIC_PADDING, y=0)

    def display_text(self, text):
        self.text_box.delete(1.0, END)
        self.text_box.insert(tkinter.END, text)
        print()

    def read_all_text(self, event=None):
        text = self.text_box.get("1.0", END)
        self._run_read_aloud_process(self._remove_new_line_characters_for_continuous_speech(text))

    def read_selected_text(self, event=None):
        sel_start, sel_end = self.text_box.tag_ranges("sel")

        if sel_start and sel_end:
            text = self.text_box.get(sel_start, sel_end)
            self._run_read_aloud_process(self._remove_new_line_characters_for_continuous_speech(text))

    @staticmethod
    def _run_read_aloud_process(text, event=None):
        read_allowed_thread = multiprocessing.Process(target=read_text, args=(text,))
        read_allowed_thread.start()
        while read_allowed_thread.is_alive():
            if keyboard.is_pressed('escape'):
                read_allowed_thread.terminate()
            else:
                continue
        read_allowed_thread.join()

    @staticmethod
    def _remove_new_line_characters_for_continuous_speech(text):
        return text.replace('\n', ' ')


class TextNavigation:
    CONSTANTS = CONSTANTS()

    def __init__(self, application, read_function_handle, width, height):
        self.application = application
        self.width = width
        self.height = height

        self._create_text_reading_options_panel(read_function_handle)

    def _create_text_reading_options_panel(self, read_function_handle):
        self.reading_options_panel = ttk.Frame(self.application, width=self.width, height=self.height)
        self.reading_options_panel.grid(row=1, column=1)
        self.reading_options_panel.grid_propagate(False)

        self.speaker = PhotoImage(file='images\\speaker.png')
        self.speaker = self.speaker.subsample(20, 20)
        self.speaker_button = ttk.Button(self.reading_options_panel, image=self.speaker,
                                         command=read_function_handle)
        self.speaker_button.grid(row=0, column=1, padx=((self.width / 2) - self.speaker.width(), 5),
                                 pady=8)
