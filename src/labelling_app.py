import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageTk, Image
import pandas as pd

class MainMenuPage(tk.Frame):
    """
    Main page that displays all the images names and its current state
    """
    def __init__(self, controller):
        tk.Frame.__init__(self)
        self.controller = controller
        self.controller.bind("<Button-1>", self.handle_click)

        # Query Bar
        self.heading = tk.Frame(controller, padx=30, pady=5)
        self.heading.pack(fill=tk.X)
        query_frame = tk.Frame(self.heading)
        query_frame.pack(side=tk.RIGHT)

        query_label = tk.Label(query_frame, text="Search")
        self.query_value = tk.StringVar()
        self.query_entry = tk.Entry(query_frame, textvariable=self.query_value, validate="key", validatecommand=(self.register(self.validate_query), "%P"))
        self.query_button = tk.Button(query_frame, text="Search", command=self.submit_query, state="disabled")
        query_label.pack()
        self.query_entry.pack(side=tk.LEFT, padx=5)
        self.query_button.pack(side=tk.RIGHT, padx=5)

        # Canvas Creation
        self.canvas = tk.Canvas(controller)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Scroll Bar implementation
        self.scrollbar = ttk.Scrollbar(self.canvas, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.current_frame = None
        self.current_index = 0
        bottom_frame = tk.Frame(self)
        self.next_page_button = tk.Button(bottom_frame, text="Next Page", command=self.next_page)
        self.prev_page_button = tk.Button(bottom_frame, text="Prev Page", command=self.prev_page)
        self.middle_button = tk.Button(self, text="Show Labelled", command=lambda: self.create_labels(True), width=15, height=2)
        self.create_labels()

        
        self.middle_button.pack(pady=5)
        bottom_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.BOTH, expand=True)
        self.prev_page_button.pack(side=tk.LEFT)
        self.next_page_button.pack(side=tk.RIGHT)
        self.pack(fill=tk.BOTH, padx=(20, 40))
        
        # Add Search Bar
        search_frame = tk.Frame(self)
        self.entry_value = tk.StringVar()
        self.entry_bar = tk.Entry(search_frame, textvariable=self.entry_value, validate="key", validatecommand=(self.register(self.validate_search), "%P"))
        self.submit_button = tk.Button(search_frame, text="Open", command=self.submit_search, state="disabled")
        self.warning = tk.Label(self, text="Please input integer 0 - 54107", foreground="red")
        self.entry_bar.pack(side=tk.LEFT, padx=5)
        self.submit_button.pack(side=tk.RIGHT, padx=5)
        search_frame.pack()

    def prev_page(self):
        """
        Go to the previous 100 images
        """
        self.current_index -= 100
        self.display_current()

    def next_page(self):
        """
        Go to the next 100 images
        """
        self.current_index += 100
        self.display_current()

    def display_current(self):
        """
        Displays the list of images according to current settings
        with labelled shown or not
        """
        if self.middle_button.cget("text") == "Show Labelled":
            self.create_labels()
        else:
            self.create_labels(True)

    def validate_search(self, value):
        """
        Validate the input in the search bar
        and enable submit button when done
        """
        if value.isdigit() and (int(value) >= 0 and int(value) <= 54107):
            self.warning.pack_forget()
            self.submit_button.configure(state="normal") 
        else:
            self.submit_button.configure(state="disabled")
            self.warning.pack()     
        return True

    def validate_query(self, value):
        """
        Validate the input in the query bar
        and enable submit button when done
        """
        if value.isdigit() and (int(value) >= 0 and int(value) <= 54007):
            self.query_button.configure(state="normal")
        else:
            self.query_button.configure(state="disabled")
        return True

    def submit_query(self):
        """
        Change the list to start from the index in the query entry
        """
        self.current_index = int(self.query_value.get())
        self.display_current()

    def submit_search(self):
        """
        Open the user's input index 
        """
        self.open_label_page(int(self.entry_value.get()))

    def handle_click(self, event):
        """
        Used to unfocus whenever any click occurs outside the entry widget (search bar)
        """
        if not isinstance(event.widget, tk.Entry):
            self.controller.focus()

    def create_labels(self, labelled=False):
        """
        Create the list of images on the main page
        """
        # Check if there are next pages or not and set the button states
        if self.current_index < 99:
            self.prev_page_button.configure(state="disabled")
        else:
            self.prev_page_button.configure(state="normal")
        if self.current_index > (54107 - 99):
            self.next_page_button.configure(state="disabled")
        else:
            self.next_page_button.configure(state="normal")

        image_indices = []
        display_names = []
        current_index = self.current_index
        if labelled:
            self.middle_button.configure(text="Hide Labelled", command=lambda: self.create_labels(False))
            while len(image_indices) < 100 and current_index < 54107:
                string = "%d.jpeg" % current_index
                if self.controller.check_if_labelled(current_index) == True:
                    string += " (labelled)"
                display_names.append(string)
                image_indices.append(current_index)
                current_index += 1
        else:
            self.middle_button.configure(text="Show Labelled", command=lambda: self.create_labels(True))
            while len(image_indices) < 100 and current_index < 54107:
                if self.controller.check_if_labelled(current_index) == False:
                    image_indices.append(current_index)
                    display_names.append("%d.jpeg" % current_index)
                current_index += 1
        indices = {k: v for (k, v) in zip(display_names, image_indices)} # type: ignore
        # Destroy previous list if there are any
        if self.current_frame:
            self.current_frame.destroy()

        # Create the frame list inside the canvas
        self.current_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.current_frame, anchor=tk.NW, width=770)
        for i in display_names:
            frame = tk.Frame(self.current_frame, highlightbackground="black", highlightthickness=1)
            text = tk.Label(frame, text=i)
            button = tk.Button(frame, text="Open/Label", command=lambda index=indices[i]: self.open_label_page(index))
            frame.pack(fill=tk.X, pady=2)
            text.pack(side=tk.LEFT)
            button.pack(side=tk.RIGHT, pady=5, padx=10)
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def open_label_page(self, index: int):
        """
        Initialize label page
        """
        print("INDEX %d CLICKED" % index)
        self.controller.to_label = index
        self.canvas.destroy()
        self.heading.destroy()
        self.scrollbar.destroy()
        self.controller.show_page(LabellingPage)

    def on_mousewheel(self, event):
        """
        Function to implement mouse wheel control
        """
        self.canvas.yview_scroll(-1 * int(event.delta/120), "units")

class LabellingPage(tk.Frame):
    """
    Page that is displayed to label the data
    """
    def __init__(self, controller):
        tk.Frame.__init__(self)
        self.pack(fill=tk.BOTH, padx=(20, 20))
        self.controller = controller
        self.index = controller.to_label

        heading = tk.Frame(self, pady=20)
        heading_text = tk.Label(heading, text="%d.jpeg" % controller.to_label, font=("Arial", 18))
        back_button = tk.Button(heading, text="Return", command=lambda: controller.show_page(MainMenuPage))
        heading.pack(fill=tk.X)
        heading_text.pack()
        back_button.place(in_=heading, anchor="nw")

        # Create Frame to display Image
        image_frame = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        image_frame.pack()
        raw_image = Image.open("../data/images/%d.jpeg" % controller.to_label)
        raw_image = raw_image.resize((400, 400))
        # plt.imshow(np.array(raw_image))
        # plt.show()
        self.current_img = ImageTk.PhotoImage(raw_image)
        image_label = tk.Label(image_frame, image=self.current_img)
        image_label.pack(pady=10, padx= 10)

        # Create switches and buttons
        self.intvar = [tk.IntVar(value=i) for i in self.initialize_labels()]
        self.create_switches()
        # submit_button = tk.Button(self, width=30, height=3, text="Submit and Continue", font=("Arial", 14), command=self.submit, borderwidth=2)
        # submit_button.pack(pady=20)
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X, pady=20)
        self.next_button = tk.Button(bottom_frame, text="Next Image", width=15, height=3, command=lambda: self.submit(True))
        self.prev_button = tk.Button(bottom_frame, text="Prev Image", width=15, height=3, command=lambda: self.submit(False))
        self.next_button.pack(side=tk.RIGHT)
        self.prev_button.pack(side=tk.LEFT)
        self.set_button_state()

    def set_button_state(self):
        if self.index == 0:
            self.prev_button.configure(state="disabled")
        else:
            self.prev_button.configure(state="normal")
        if self.index > 54007:
            self.next_button.configure(state="disabled")
        else:
            self.next_button.configure(state="normal")

    def submit(self, state: bool):
        """
        Save the labels created by the user locally (not saved into file)
        Depending on the state parameter:
        True = go to next page
        False = go to previous page
        """
        self.controller.label_data["label"][self.index] = str([i.get() for i in self.intvar])
        print(self.controller.label_data["label"][self.index])
        if state:
            self.controller.to_label += 1
        else:
            self.controller.to_label -= 1
        self.controller.show_page(LabellingPage)

    def initialize_labels(self):
        """
        Returns label if it already exists in labels.csv
        otherwise returns a list of 12 integers with the value of 0
        """
        if self.controller.check_if_labelled(self.index):
            return eval(self.controller.label_data["label"][self.index])
        return [0 for i in range(len(self.controller.label_names))]
    
    def create_switches(self):
        """
        Create switches and give initial states depending on if it has been labelled or not
        """
        label_names = self.controller.label_names
        idx = 0
        frame = tk.Frame(self)
        frame.pack(pady=(10, 0))
        for i in range(3):
            for j in range(4):
                if idx == 11:
                    return
                frametest = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
                switch = tk.Checkbutton(frametest, text=label_names[idx], variable=self.intvar[idx])
                frametest.grid(row=i, column=j, sticky="nsew")
                switch.pack(side=tk.LEFT)
                frame.columnconfigure(j, minsize=106)
                idx += 1



class Application(tk.Tk):
    """
    The Main application and functions
    """
    LABEL_NAMES = [
        'Bicycle', 'Bridge', 'Bus', 'Car', 'Crosswalk', 
        'Hydrant', 'Motorcycle', 'Stairs', 'Tractors',
        'Traffic Light', 'Other'
    ]

    @property
    def label_names(self):
        return self.LABEL_NAMES

    def __init__(self):
        tk.Tk.__init__(self)
        self.title("CAPTCHA multi-labelling application")
        self.geometry("800x700")
        self.resizable(False, False)
        self.label_data = pd.read_csv("../data/labels.csv")
        self.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.current_page = None
        self.to_label = None
        self.show_page(MainMenuPage)
    
    def show_page(self, page_class):
        """
        Change page into the page_class passed through the argument
        """
        if self.current_page:
            self.current_page.destroy()
        self.current_page = page_class(self)

    def save_csv(self):
        """
        Save current labels progress into the csv
        """
        self.label_data.to_csv("../data/labels.csv", index=False)

    def exit_app(self):
        """
        Method to exit the application and saves the current csv progress
        """
        query = messagebox.askquestion("Exit Application", "Are you sure you want to save and exit?")
        if query == "yes":
            self.save_csv()
            self.destroy()

    def check_if_labelled(self, index: int) -> bool:
        """
        Check if an image index is already labeled
        returns Boolean
        """
        if self.label_data["label"].isnull().values[index]:
            return False
        return True
            
# MAIN DRIVER
if __name__ == "__main__":
    app = Application()
    app.mainloop()