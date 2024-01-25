# Updated code for a modern dark-themed UI

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk

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

class Annotation:
    def __init__(self, canvas, x, y, text, img_width, img_height):
        self.canvas = canvas
        self.text = text
        self.original_coords = (x, y)
        self.draw_annotation(x, y)
        self.bind_events()
        self.relative_coords = (x / img_width, y / img_height)

    def draw_annotation(self, x, y):
        self.text_id = self.canvas.create_text(x + 130, y, text=self.text, fill="#FFFFFF", font=('Arial', 24), anchor=tk.W)
        bbox = self.canvas.bbox(self.text_id)
        padded_bbox = (bbox[0] - 10, bbox[1] - 8, bbox[2] + 10, bbox[3] + 8)
        self.rect_id = rounded_rectangle(self.canvas, *padded_bbox, radius=10, fill="#FF3333")
        self.canvas.tag_lower(self.rect_id, self.text_id)
        self.arrow = self.canvas.create_line(bbox[0], y, x, y, arrow=tk.LAST, fill="#FF3333", width=3)

    def on_text_click(self, event):
        new_text = simpledialog.askstring("Input", "Edit annotation text:", initialvalue=self.text)
        if new_text:
            self.text = new_text
            self.canvas.itemconfig(self.text_id, text=self.text)
            self.canvas.coords(self.rect_id, self.canvas.bbox(self.text_id))

    def on_drag(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.move(self.text_id, x - self.canvas.bbox(self.text_id)[0] - 5, y - self.canvas.bbox(self.text_id)[1] - 5)
        self.canvas.coords(self.rect_id, self.canvas.bbox(self.text_id))
        self.canvas.coords(self.arrow, *self.canvas.coords(self.arrow)[:2], x, y)

    def on_arrow_drag(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.coords(self.arrow, *self.canvas.coords(self.arrow)[:2], x, y)

    def on_rect_click(self, event):
        self.canvas.delete(self.rect_id)
        self.canvas.delete(self.text_id)
        self.canvas.delete(self.arrow)

    def bind_events(self):
        self.canvas.tag_bind(self.text_id, "<Button-1>", self.on_text_click)
        self.canvas.tag_bind(self.rect_id, "<Button-1>", self.on_rect_click)
        self.canvas.tag_bind(self.text_id, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.rect_id, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.arrow, "<B1-Motion>", self.on_arrow_drag)

class ImageAnnotationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool Enhanced")
        self.root.geometry("1280x720")
        self.root.configure(bg="#2E2E2E")  # Dark theme background

        menu_bar = tk.Menu(root, bg="#3C3C3C", fg="#FFFFFF")
        root.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0, bg="#3C3C3C", fg="#FFFFFF", activebackground="#555555", activeforeground="#FFFFFF")
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image", command=self.load_image)
        file_menu.add_command(label="Save", command=self.save_image)

        toolbar = tk.Frame(root, bg="#3C3C3C")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        self.zoom_in_btn = tk.Button(toolbar, text="Zoom In", command=self.zoom_in, bg="#3C3C3C", fg="#FFFFFF", activebackground="#555555", relief=tk.FLAT)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.zoom_out_btn = tk.Button(toolbar, text="Zoom Out", command=self.zoom_out, bg="#3C3C3C", fg="#FFFFFF", activebackground="#555555", relief=tk.FLAT)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.canvas = tk.Canvas(self.root, bg="#1A1A1A", cursor="cross", highlightthickness=0)  # Dark theme canvas
        self.canvas.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.annotate_image)

        self.image_path = None
        self.img = None
        self.img_tk = None
        self.image_id = None
        self.annotations = []

        self.zoom_level = 1
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<B3-Motion>", self.pan)

        self.undo_stack = []
        self.redo_stack = []

        edit_menu = tk.Menu(menu_bar, tearoff=0, bg="#3C3C3C", fg="#FFFFFF", activebackground="#555555", activeforeground="#FFFFFF")
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_path = file_path
            self.img = Image.open(self.image_path)
            self.img = self.resize_image(self.img, self.canvas.winfo_width(), self.canvas.winfo_height())
            self.img_tk = ImageTk.PhotoImage(self.img)
            if self.image_id:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, anchor=tk.CENTER, image=self.img_tk)

    def resize_image(self, img, max_width, max_height):
        img_aspect = img.width / img.height
        canvas_aspect = max_width / max_height
        if img_aspect > canvas_aspect:
            return img.resize((max_width, round(max_width / img_aspect)))
        else:
            return img.resize((round(max_height * img_aspect), max_height))

    def save_image(self):
        if self.img:
            save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")])
            if save_path:
                self.img.save(save_path)
                messagebox.showinfo("Success", "Image saved successfully!", icon=messagebox.INFO)

    def annotate_image(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        text = simpledialog.askstring("Input", "Enter annotation text:")
        if text:
            annotation = Annotation(self.canvas, x, y, text, self.img.width, self.img.height)
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
                new_x = cx + (annotation.original_coords[0] - cx) * self.zoom_level
                new_y = cy + (annotation.original_coords[1] - cy) * self.zoom_level
                self.canvas.delete(annotation.arrow)
                self.canvas.delete(annotation.text_id)
                self.canvas.delete(annotation.rect_id)
                annotation.draw_annotation(new_x, new_y)
                annotation.bind_events()

    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

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
                item.draw_annotation(*item.original_coords)
                item.bind_events()
                self.undo_stack.append((action, item))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnnotationApp(root)
    root.mainloop()

