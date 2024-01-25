import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import tkinter.colorchooser as colorchooser
from tkinter import font
import io

def rounded_rectangle(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [x1 + radius, y1,
              x2 - radius, y1,
              x2, y1,
              x2, y1 + radius,
              x2, y2 - radius,
              x2, y2,
              x2 - radius, y2,
              x1 + radius, y2,
              x1, y2,
              x1, y2 - radius,
              x1, y1 + radius,
              x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

class AnnotationSettings(tk.Toplevel):
    def __init__(self, parent, selected_annotation):
        super().__init__(parent.root, bg="#3C3C3C")
        self.title("Annotation Settings")
        self.selected_annotation = selected_annotation
        self.parent = parent
        self.center_window()
        self.attributes("-topmost", True)
        
        # Fonts
        custom_font = font.Font(family="Helvetica", size=10, weight="bold")
        
        # Text input for changing annotation text
        tk.Label(self, text="Annotation Text:", bg="#3C3C3C", fg="white").pack(padx=10, pady=5, anchor=tk.W)
        self.annotation_input = tk.Entry(self, bg="#555555", fg="white", insertbackground="white")
        self.annotation_input.pack(padx=10, pady=5, fill=tk.X)
        self.annotation_input.insert(0, selected_annotation.text)
        
        # Slider for adjusting size (Note: Sliders don't support bg in the native tkinter)
        self.size_slider = tk.Scale(self, from_=5, to=100, orient=tk.HORIZONTAL, label="Size", fg="#3C3C3C")
        self.size_slider.set(selected_annotation.size)
        self.size_slider.pack(padx=10, pady=5)
        
        # # Slider for adjusting arrow length
        # self.arrow_length_slider = tk.Scale(self, from_=50, to=800, orient=tk.HORIZONTAL, label="Arrow Length", fg="#3C3C3C")
        # self.arrow_length_slider.set(selected_annotation.arrow_length)
        # self.arrow_length_slider.pack(padx=10, pady=5)
        
        # Slider for adjusting arrow width
        self.arrow_width_slider = tk.Scale(self, from_=2, to=100, orient=tk.HORIZONTAL, label="Arrow width", fg="#3C3C3C")
        self.arrow_width_slider.set(selected_annotation.arrow_th)
        self.arrow_width_slider.pack(padx=10, pady=5)
        
        # Color Picker Button
        self.color = selected_annotation.color
        self.color_btn = tk.Button(self, text="Pick Color", command=self.pick_color, bg=self.color, 
                                   fg="white", font=custom_font, relief=tk.GROOVE, padx=10, pady=5)
        self.color_btn.pack(padx=10, pady=5)
        
        # Binding hover effect
        self.color_btn.bind("<Enter>", self.on_enter)
        self.color_btn.bind("<Leave>", self.on_leave)
        
        # OK button to apply changes
        self.ok_btn = tk.Button(self, text="OK", command=self.apply_changes, bg="#555555", fg="white", 
                                font=custom_font, relief=tk.GROOVE, padx=10, pady=5)
        self.ok_btn.pack(padx=10, pady=10)

    def on_enter(self, event):
        """Change the button color when mouse hovers over it."""
        self.color_btn.config(bg="#444444")  # Darker shade when hovered

    def on_leave(self, event):
        """Reset the button color when mouse leaves it."""
        self.color_btn.config(bg=self.color)

    def pick_color(self):
        """Open a color picker dialog and store the chosen color."""
        color = colorchooser.askcolor()[1]
        if color:
            self.color_btn.config(bg=color)
            self.color = color  # Store the chosen color

    def center_window(self):
        """Center the window on the screen."""
        # Get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate x and y coordinates for the window
        x = (screen_width / 2) - (self.winfo_reqwidth() / 2)
        y = (screen_height / 2) - (self.winfo_reqheight() / 2)

        # Set the window's position
        self.geometry('+%d+%d' % (x, y))

    def apply_changes(self):
        self.selected_annotation.text = self.annotation_input.get()
        self.selected_annotation.size = self.size_slider.get()
        # self.selected_annotation.arrow_length = self.arrow_length_slider.get()
        self.selected_annotation.arrow_th = self.arrow_width_slider.get()
        self.selected_annotation.color = self.color
        # Update the visual representation of the annotation
        cx, cy = self.parent.canvas.winfo_width() // 2, self.parent.canvas.winfo_height() // 2
        self.parent.canvas.delete(self.selected_annotation.arrow)
        self.parent.canvas.delete(self.selected_annotation.text_id)
        self.parent.canvas.delete(self.selected_annotation.rect_id)
        self.selected_annotation.draw_annotation(  
            self.selected_annotation.current_coords[0], 
            self.selected_annotation.current_coords[1], 
            self.selected_annotation.arrow_endpoint[0], 
            self.selected_annotation.arrow_endpoint[1],
            self.selected_annotation.size,
            self.selected_annotation.arrow_length,
            cx, cy,
            self.parent.zoom_level,
            self.selected_annotation.color ,
            self.selected_annotation.arrow_th
        )
        
        # Change the color
        # self.parent.canvas.itemconfig(self.selected_annotation.rect_id, fill=self.color)
        # self.parent.canvas.itemconfig(self.selected_annotation.arrow, fill=self.color)
        
        # Rebind events
        self.selected_annotation.bind_events()
        
        # Close the settings window
        self.destroy()

class Annotation:
    def __init__(self, canvas, app, x, y, text,size,color,arrow_th,arrow_length,arrow_endpoint, img_width, img_height, cx, cy, zoom_level):
        self.app = app 
        self.canvas = canvas
        self.text = text
        self.size=size
        self.color=color 
        self.arrow_th=arrow_th 
        self.current_coords =(x,y)
        self.arrow_length=arrow_length 
        self.selected = False
        self.arrow_endpoint =arrow_endpoint 
        self.draw_annotation(x , y ,arrow_endpoint[0] ,arrow_endpoint[1] ,self.size,self.arrow_length,cx,cy,zoom_level,self.color,self.arrow_th)
        self.bind_events()
        self.relative_coords = (x / img_width, y / img_height)
        self.drag_data = {"x": 0, "y": 0, "item": None}

    def draw_annotation(self, x, y, x_end_arrow, y_end_arrow,size,arrow_length,cx, cy,zoom_level,color,arrow_th):
        new_length = int(arrow_length * zoom_level)
        new_size = int(size * zoom_level)
        new_th=int(arrow_th * zoom_level)
        # Calculate new position for text based on current_coords
        new_x = cx + (x - cx) * zoom_level
        new_y = cy + (y - cy) * zoom_level
        
        # Calculate new position for arrow endpoint based on arrow_endpoint
        arrow_end_x = cx + (x_end_arrow - cx) * zoom_level
        arrow_end_y = cy + (y_end_arrow - cy) * zoom_level
        
        self.text_id = self.canvas.create_text(new_x + new_length, new_y, text=self.text, fill="#FFFFFF", font=('Arial', new_size), anchor=tk.W)
        bbox = self.canvas.bbox(self.text_id)
        padded_bbox = (bbox[0] - new_size/2, bbox[1] - new_size/2, bbox[2] + new_size/2, bbox[3] + new_size/2)
        self.rect_id = rounded_rectangle(self.canvas, *padded_bbox, radius=new_size/2, fill=color)
        self.canvas.tag_lower(self.rect_id, self.text_id)
        arrow_shape = (2*new_th, 3*new_th, new_th)  # Example values; adjust for your needs

        self.arrow = self.canvas.create_line(
    bbox[0] + ((bbox[2] - bbox[0]) / 2), new_y, 
    arrow_end_x, arrow_end_y, 
    arrow=tk.LAST, 
    fill=color, 
    width=new_th, 
    smooth=True, 
    capstyle=tk.ROUND, 
    joinstyle=tk.ROUND,
    arrowshape=arrow_shape
)
        self.canvas.tag_lower(self.arrow, self.text_id)

    def bind_events(self):
        self.canvas.tag_bind(self.text_id, '<Button-3>', self.on_start_drag)
        self.canvas.tag_bind(self.rect_id, '<Button-3>', self.on_start_drag)
        self.canvas.tag_bind(self.arrow, '<Button-3>', self.on_start_drag)
        self.canvas.tag_bind(self.text_id, '<B3-Motion>', self.on_drag)
        self.canvas.tag_bind(self.rect_id, '<B3-Motion>', self.on_drag)
        self.canvas.tag_bind(self.arrow, '<B3-Motion>', self.on_drag)

    def on_select(self, event=None):
        # Deselect the previously selected annotation
        for ann in self.canvas.annotations:
            if ann.selected:
                ann.deselect()

        # Select the current annotation
        self.select()
        
        # Open the Annotation Settings window
        settings_window = AnnotationSettings(self.app, self)

    def deselect(self):
        self.selected = False
        self.canvas.itemconfig(self.rect_id, outline="", width=1)

    def on_start_drag(self, event):
        # Record the initial position of the cursor and the current item being dragged.
        
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]
        for ann in self.app.annotations:
            ann.deselect()

    def on_drag(self, event):
        
        # Calculate the distance moved by the mouse.
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        
        # Move the annotation elements (rectangle, text, arrow) by the calculated distances.
        if self.drag_data["item"] in [self.text_id, self.rect_id]:
            self.canvas.move(self.rect_id, dx, dy)
            self.canvas.move(self.text_id, dx, dy)
            x0, y0, x1, y1 = self.canvas.coords(self.arrow)
            self.canvas.coords(self.arrow, x0 + dx, y0 + dy, x1, y1)
            self.current_coords = (self.current_coords[0] + dx, self.current_coords[1] + dy)
        elif self.drag_data["item"] == self.arrow:
            x0, y0, x1, y1 = self.canvas.coords(self.arrow)
            self.canvas.coords(self.arrow, x0, y0, x1 + dx, y1 + dy)
            self.arrow_endpoint = (x1 + dx, y1 + dy)

    def select(self):
        self.selected = True
        self.canvas.itemconfig(self.rect_id, outline="#FFFFFF", width=2)

    def is_clicked(self, x, y):
        bbox = self.canvas.bbox(self.rect_id)
        return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]

class RoundedButton(tk.Canvas):
    def __init__(self, master=None, command=None, text="", **kwargs):
        super().__init__(master, bd=0, highlightthickness=0, bg="#3C3C3C", **kwargs)
        
        self.command = command
        self.text = text
        
        # Initial drawing of the button
        self.draw_button()
        
        # Bind events for button behavior
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

    def draw_button(self, color="#3C3C3C"):
        self.delete("all")
        self.rounded_rect = rounded_rectangle(self, 0, 0, self.winfo_reqwidth(), self.winfo_reqheight(), 10, fill=color)
        self.create_text(self.winfo_reqwidth() // 2, self.winfo_reqheight() // 2, text=self.text, fill="#FFFFFF", font=('Arial', 12))

    def on_enter(self, event):
        self.draw_button("#555555")

    def on_leave(self, event):
        self.draw_button("#3C3C3C")

    def on_click(self, event):
        self.draw_button("#444444")

    def on_release(self, event):
        self.draw_button("#555555")
        if self.command:
            self.command()

    def is_clicked(self, x, y):
        bbox = self.canvas.bbox(self.rect_id)
        return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]

class ImageAnnotationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool Enhanced")
        # self.root.attributes('-fullscreen', True)
        self.root.geometry("1280x720")
        self.root.configure(bg="#2E2E2E")  # Dark theme background
        self.drag_data2 = {"x": 0, "y": 0}
        toolbar = tk.Frame(root, bg="#3C3C3C")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        # Existing buttons
        self.open_image_btn = RoundedButton(toolbar, text="Open Image", command=self.load_image, width=100, height=30)
        self.open_image_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.save_btn = RoundedButton(toolbar, text="Save", command=self.save_image, width=60, height=30)
        self.save_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.undo_btn = RoundedButton(toolbar, text="Undo", command=self.undo, width=60, height=30)
        self.undo_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.redo_btn = RoundedButton(toolbar, text="Redo", command=self.redo, width=60, height=30)
        self.redo_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.zoom_in_btn = RoundedButton(toolbar, text="Zoom In", command=self.zoom_in, width=80, height=30)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.zoom_out_btn = RoundedButton(toolbar, text="Zoom Out", command=self.zoom_out, width=90, height=30)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.exit_btn = RoundedButton(toolbar, text="Exit", command=self.close_app, width=60, height=30)
        self.exit_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        self.canvas = tk.Canvas(self.root, bg="#1A1A1A", cursor="cross", highlightthickness=0)  # Dark theme canvas
        self.canvas.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        self.image_path = None
        self.img = None
        self.img_tk = None
        self.image_id = None
        self.annotations = []
        self.canvas.annotations = self.annotations
        self.zoom_level = 1
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<Button-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.continue_pan)
        self.canvas.bind("<ButtonRelease-1>", self.check_click_or_drag)
        self.undo_stack = []
        self.redo_stack = []

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_path = file_path
            self.img = Image.open(self.image_path)
            # self.img = self.resize_image(self.img, self.canvas.winfo_width(), self.canvas.winfo_height())
            self.img_tk = ImageTk.PhotoImage(self.img)
            
            # Delete any existing annotations before loading a new image
            if self.annotations:
                for annotation in self.annotations:
                    self.canvas.delete(annotation.rect_id)
                    self.canvas.delete(annotation.text_id)
                    self.canvas.delete(annotation.arrow)
                self.annotations.clear()

            # Delete the previous image if present
            if self.image_id:
                self.canvas.delete(self.image_id)
            
            # Create the new image on the canvas
            self.image_id = self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, anchor=tk.CENTER, image=self.img_tk)

    def close_app(self):
        response = messagebox.askokcancel("Confirm Exit", "If you exit, you are going to lose any unsaved changes. Are you sure?")
        if response:
            self.root.quit()
    
    def resize_image(self, img, max_width, max_height):
        img_aspect = img.width / img.height
        canvas_aspect = max_width / max_height
        if img_aspect > canvas_aspect:
            return img.resize((max_width, round(max_width / img_aspect)))
        else:
            return img.resize((round(max_height * img_aspect), max_height))


    def save_image(self):
        # Check if there's an image loaded
        if self.image_id:
            # Create a filename for saving
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                    filetypes=[("PNG files", "*.png"),
                                                                ("JPEG files", "*.jpg"),
                                                                ("All files", "*.*")])
            if file_path:
                # Backup current zoom level and window size
                original_zoom = self.zoom_level
                original_window_size = self.root.geometry()

                # Reset zoom and center the image
                self.zoom_level = 1
                self.update_image_zoom()

                # Create a higher-resolution canvas
                high_res_factor = 3  # Factor to increase resolution
                high_res_width = self.canvas.winfo_width() * high_res_factor
                high_res_height = self.canvas.winfo_height() * high_res_factor
                high_res_canvas = tk.Canvas(self.root, width=high_res_width, height=high_res_height, bg="#1A1A1A")

                # Draw the high-resolution image on the canvas
                high_res_canvas_image = self.img.resize((self.img.width * high_res_factor, self.img.height * high_res_factor))
                high_res_img_tk = ImageTk.PhotoImage(high_res_canvas_image)
                high_res_canvas.create_image(high_res_width // 2, high_res_height // 2, image=high_res_img_tk)

                # Render annotations on high-res canvas
                temp_annotations = []  # List to hold temporary annotations for high_res_canvas
                for annotation in self.annotations:
                    cx, cy = high_res_width // 2, high_res_height // 2
                    size=annotation.size* high_res_factor
                    color=annotation.color
                    arrow_th=annotation.arrow_th* high_res_factor
                    arrow_length=annotation.arrow_length* high_res_factor
                    arrow_endpoint=(annotation.arrow_endpoint[0]* high_res_factor,annotation.arrow_endpoint[1]* high_res_factor)
                    temp_annotation = Annotation(high_res_canvas, self,
                                                annotation.current_coords[0] * high_res_factor,
                                                annotation.current_coords[1] * high_res_factor,
                                                annotation.text,
                                                size,color,arrow_th,arrow_length,arrow_endpoint,
                                                self.img.width * high_res_factor, 
                                                self.img.height * high_res_factor,
                                                cx, cy,
                                                self.zoom_level)
                    temp_annotation.color = annotation.color
                    temp_annotation.arrow_th = annotation.arrow_th
                    temp_annotation.size = annotation.size
                    temp_annotation.arrow_length = annotation.arrow_length
                    temp_annotations.append(temp_annotation)

                # Temporarily resize the window to fit the high-res canvas
                self.root.geometry(f"{high_res_width}x{high_res_height}")
                self.canvas.pack_forget()
                high_res_canvas.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
                self.root.update_idletasks()

                # Export high-res canvas content to postscript
                ps = high_res_canvas.postscript(colormode='color', width=high_res_width, height=high_res_height)

                # Convert to image using PIL
                img = Image.open(io.BytesIO(ps.encode('utf-8')))

                # Crop to image size
                
                # Save the image
                img.save(file_path)

                # Restore original canvas, zoom level, and window size
                high_res_canvas.pack_forget()
                self.canvas.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
                self.zoom_level = original_zoom
                self.update_image_zoom()
                self.root.geometry(original_window_size)

    def annotate_image(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Check if the click is on any annotation
        for ann in self.annotations:
            if ann.is_clicked(x, y):
                ann.on_select()
                return
            
        for ann in self.annotations:
            ann.deselect()
        text = simpledialog.askstring("Input", "Enter annotation text:")
        if text:
            cx, cy = self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2
            size=30
            color="#FF3333"
            arrow_th=10
            arrow_length=130
            arrow_endpoint=(x,y)
            annotation = Annotation(self.canvas,self, x, y, text,size,color,arrow_th,arrow_length,arrow_endpoint, self.img.width, self.img.height,cx, cy,self.zoom_level)
            self.annotations.append(annotation)
            self.undo_stack.append(("create", annotation))
            self.redo_stack.clear()

    def zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self.zoom_level += 0.1
        self.update_image_zoom()

    def zoom_out(self):
        self.zoom_level -= 0.1
        self.update_image_zoom()

    def update_image_zoom(self):
        if self.img:
            new_width = int(self.img.width * self.zoom_level)
            new_height = int(self.img.height * self.zoom_level)
            resized_img = self.img.resize((new_width, new_height), Image.LANCZOS)
            self.img_tk = ImageTk.PhotoImage(resized_img)
            self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, anchor=tk.CENTER, image=self.img_tk)
            for annotation in self.annotations:
                cx, cy = self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2
                self.canvas.delete(annotation.arrow)
                self.canvas.delete(annotation.text_id)
                self.canvas.delete(annotation.rect_id)
                annotation.draw_annotation( annotation.current_coords[0], annotation.current_coords[1], annotation.arrow_endpoint[0], annotation.arrow_endpoint[1],annotation.size,annotation.arrow_length,cx, cy,self.zoom_level,annotation.color,annotation.arrow_th)
                # Rebind events
                annotation.bind_events()

    def start_pan(self, event):
        self.drag_data2["x"] = event.x
        self.drag_data2["y"] = event.y

        # If not on an annotation, start a potential drag
        self.canvas.scan_mark(event.x, event.y)

    def continue_pan(self, event):
        # Adjust the position of the canvas content using scan_dragto
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def check_click_or_drag(self, event):
        if abs(event.x - self.drag_data2["x"]) < 5 and abs(event.y - self.drag_data2["y"]) < 5:
            self.annotate_image(event)

    def undo(self):
        if self.undo_stack:
            action, item = self.undo_stack.pop()
            if action == "create":
                self.annotations.remove(item)
                self.canvas.delete(item.rect_id)
                self.canvas.delete(item.text_id)
                self.canvas.delete(item.arrow)
                self.redo_stack.append((action, item))

    def redo(self):
        if self.redo_stack:
            action, item = self.redo_stack.pop()
            if action == "create":
                self.annotations.append(item)

                cx, cy= self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2

                self.canvas.delete(item.arrow)
                self.canvas.delete(item.text_id)
                self.canvas.delete(item.rect_id)
                
                item.draw_annotation( item.current_coords[0], item.current_coords[1], item.arrow_endpoint[0], item.arrow_endpoint[1],item.size,item.arrow_length,cx, cy,self.zoom_level,item.color,item.arrow_th)

                item.bind_events()
                self.undo_stack.append((action, item))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnnotationApp(root)
    root.mainloop()