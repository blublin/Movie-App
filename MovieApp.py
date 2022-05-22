"""
Final project!
CIS 41B Adv Python
Mar 23, 2021

Ben Lublin
Maria Gorbunova

Enjoy organizing your movie choices!:)

Free avatars from Freepik user sentavio: https://www.freepik.com/sentavio

Frontend - GUI to interact with user
Written by Ben, with help and reviewed by Maria
"""
import os
import sys
import math
import time
import shutil # for copying avatar
import threading
import tkinter as tk
from io import BytesIO
from tkinter import ttk
import tkinter.filedialog
from datetime import datetime # get current year
from PIL import Image, ImageTk # Allows use of jpg, jpeg, png, etc
import tkinter.messagebox as tkmb 
from backend import APITalker, DBTalker


FRAME_HEIGHT = 790
A_HEIGHT = 60
C_HEIGHT = FRAME_HEIGHT - A_HEIGHT - 10
S_WIDTH = 150
B_WIDTH = 1030
PXY = 5
PH = 2.5


class RootWindow(tk.Tk):
    '''
    Main App window with 4 main frames
    '''
    
    def __init__(self):
        '''
        Create instance of backend classes to allow access to data
        Create initial frames and place them in main window
        
        '''
        super().__init__()
        
        # Window
        win_width = 1200
        win_height = 800
        self.title('Movie App')
        # self.geometry('1200x800')
        self.resizable(False,False)
        
        # Gets both half the screen width/height and window width/height
        positionRight = int(self.winfo_screenwidth()/2 - win_width/2)
        positionDown = int(self.winfo_screenheight()/2.2 - win_height/2)
         
        # Positions the window in the center of the page.
        self.geometry(f"{win_width}x{win_height}+{positionRight}+{positionDown}")        
        
        # Use backend for data
        self.api_obj = APITalker()
        self.db_obj = DBTalker(self.api_obj)
        self.genre_dict = {t[1]:t[0] for t in self.db_obj.getGenres()}
        ## { Genre : ID }
        
        # search button image
        sb_file = "search_button_30px.png"
        self.search_image = ImageTk.PhotoImage(file=sb_file)
        
        self.home_already_run = False

        ### TTK Styles
        main_style = ttk.Style()
        if os.name == 'nt': # If Windows OS
            main_style.theme_use('winnative')
        else:
            main_style.theme_use('aqua')
        ## ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
        self.s1 = ttk.Style()
        # self.s1.configure('main.TFrame', background='navajo white')        
        
        self.make_side_area() # Frame 1 > root
        self.make_body_area() # Frame 2 > root
        self.make_api_area() # Frame 3 > frame 2
        self.make_content_area() # Frame 4 > frame 2
        
        ### Weight
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)   

    ### TTK Frames
    # Frame 1
    def make_side_area(self):
        '''
        Create left side general selection frame with:
        User, Home Button, Watched Button, To Watch Button
        
        Clicking on buttons changes content frame
        '''
        small_y_space = 10
        big_y_space = 75
        half_y_space = 75

        self.s1.configure('side.TButton', height=40, font=20)
        side_frame = ttk.Frame(self, height=FRAME_HEIGHT, width=S_WIDTH, cursor='tcross', relief='groove')
        side_frame.config(style='main.TFrame')      
        
        ## Frame 1 Widgets
        self.user_name = tk.StringVar() # default value is ''  
        
        un, avatar_path = self.user_profile() # get username and avatar
        # user profile name
        self.user_name.set(un)
        name_label = ttk.Label(side_frame, textvariable=self.user_name, font=25)
        # user profile image
        display_avatar = ttk.Label(side_frame)
        avatar_image = Image.open(avatar_path)
        avatar_image = avatar_image.resize((50,50), Image.ANTIALIAS)
        self.avatar = ImageTk.PhotoImage(avatar_image)
        display_avatar['image'] = self.avatar
        # Buttons!
        home_button = ttk.Button(side_frame, text="Home", style='side.TButton')
        to_watch_button = ttk.Button(side_frame, text="Movies\nTo Watch", style='side.TButton') # Add command
        watched_button = ttk.Button(side_frame, text="Movies\nSeen", style='side.TButton') # Add Command
        
        home_button.config(command=self.content_fill_home)
        to_watch_button.config(command=lambda:self.content_fill_from_db(watched=0))
        watched_button.config(command=lambda:self.content_fill_from_db(watched=1))
        
        ### Grid
        name_label.grid(row=0, column=1, padx=(5,3), pady=(small_y_space,small_y_space))
        display_avatar.grid(row=1, column=1, padx=(3,5), pady=(small_y_space,big_y_space))
        home_button.grid(row=2, column=1, columnspan=2, pady=big_y_space)
        to_watch_button.grid(row=3, column=1, columnspan=2, pady=big_y_space)
        watched_button.grid(row=4, column=1, columnspan=2, pady=big_y_space)
        
        side_frame.columnconfigure(0, weight=1)
        side_frame.columnconfigure(3, weight=1)
        
        side_frame.pack_propagate(0)
        side_frame.pack(fill='both', side='left', expand=True, padx=PXY, pady=PXY)
        
    # Frame 2
    def make_body_area(self):
        '''
        Mainly to hold API and Content frames
        '''
        s2 = ttk.Style()
        s2.configure('body.TFrame', background='red')        
        self.body_frame = ttk.Frame(self, height=FRAME_HEIGHT, width=B_WIDTH)
        self.body_frame.config(style='main.TFrame')
        
        self.body_frame.pack(fill='both', side='right', padx=PXY, pady=PXY)
        
    # Frame 3
    def make_api_area(self):
        '''
        Top search bar area, allowing users to search by name or details
        '''
        s3 = ttk.Style()
        s3.configure('api.TFrame', background='green')
        # s3.configure('search.TFrame', background='orange')
        api_frame = ttk.Frame(self.body_frame, height=A_HEIGHT, width=B_WIDTH)
        api_frame.config(style='main.TFrame')
        
        ## Frame 3 Widgets
        # Search Selector RadioButtons
        self.search_type = tk.IntVar()
        rb1=ttk.Radiobutton(api_frame, text="Search by name", variable=self.search_type, value=1)
        rb1.config(width=18, command=self.search_by_name)
        rb2=ttk.Radiobutton(api_frame, text="Search by details", variable=self.search_type, value=2)
        rb2.config(width=18, command=self.search_by_details)
        self.search_type.set(1)
        # Search Frame
        self.search_frame = ttk.Frame(api_frame, height=A_HEIGHT, width=B_WIDTH-300)
        self.search_frame.config(style='main.TFrame')
        self.search_by_name()
        # Search Button
        search_button = ttk.Button(api_frame, text="Search!", image=self.search_image, compound='top')
        search_button.config(command=lambda :self.create_search(s_type=self.search_type.get()))
        
        ### Positions
        rb1.grid(row=1, column=1, padx=30)
        rb2.grid(row=2, column=1, padx=30)
        self.search_frame.grid(row=1, column=2, rowspan=2, sticky='w')
        search_button.grid(row=1, column=3, rowspan=2, padx=(30,0))
        
        ### Placement configurations
        self.search_frame.pack_propagate(0)
        api_frame.grid_propagate(0)
        api_frame.grid(sticky='nsew', padx=PXY, pady=PH)      
        
        api_frame.grid_rowconfigure(0, weight=1)
        api_frame.grid_rowconfigure(3, weight=1)
        api_frame.grid_columnconfigure(4, weight=1)
        api_frame.grid_columnconfigure(4, weight=1)          

    # Frame 4
    def make_content_area(self):
        '''
        Main display area, constantly updated depending on which button is pressed
        '''
        s4 = ttk.Style()
        s4.configure('content.TFrame', background='blue')        
        self.content_frame = ttk.Frame(self.body_frame, height=C_HEIGHT, width=B_WIDTH-100)
        self.content_frame.config(style='main.TFrame')
        
        self.content_frame.grid_propagate(0)
        self.content_frame.grid(sticky='nsew', padx=PXY, pady=PH)
        
        self.content_fill_home()
        
    def search_by_name(self):
        '''
        Display Entry text box for searching by name.
        Clears all other widgets in the search_frame (inside api frame)
        '''
        for widget in self.search_frame.winfo_children():
            widget.destroy()
            
        # Movie Entry
        self.default_mn_text = "Enter movie name"
        self.movie_name = tk.StringVar()
        self.movie_name.set(self.default_mn_text)
        self.api_name_entry = ttk.Entry(self.search_frame, textvariable=self.movie_name, width=30)
        
        ### Binds
        self.api_name_entry.bind("<Return>", lambda x:self.create_search(event=x,s_type=1))
        self.api_name_entry.bind("<1>", self.clear_entry)
        self.search_frame.bind("<1>", self.check_name)

        ### Positions
        self.api_name_entry.pack(fill='x', expand=True)
        
    def search_by_details(self):
        '''
        Display Optionmenu, Combobox, Checkbutton and Scale for searching by details.
        Clears all other widgets in the search_frame (inside api frame)
        '''        
        for widget in self.search_frame.winfo_children():
            widget.destroy()  
            
        # Genre Optionmenu
        self.genre_value = tk.StringVar()
        def_genre = "Select a genre"
        self.genres = [genre for genre in sorted(self.genre_dict)]
        self.genres.insert(0,def_genre)
        self.genre_dropdown = ttk.OptionMenu(self.search_frame, self.genre_value, self.genres[0], *self.genres)
        
        # Year Combobox
        default_year_text = "Year of Movie"
        self.movie_year = tk.StringVar()
        self.api_year_combo = ttk.Combobox(self.search_frame, textvariable=self.movie_year, width=15, state='readonly')
        self.years = sorted([str(i) for i in range(1900, datetime.today().year+1)], reverse=True)
        self.years.insert(0,default_year_text)
        self.api_year_combo['values'] = self.years
        self.movie_year.set(default_year_text)
        
        # Rating Scale CheckButton
        self.chkbtn_value = tk.IntVar()
        self.chkbtn_text = tk.StringVar()
        self.chkbtn_text.set("Rating Scale Disabled")
        rating_chkbtn = ttk.Checkbutton(self.search_frame, width=20, textvariable=self.chkbtn_text, variable=self.chkbtn_value, command=self.scale_on_off)
        self.chkbtn_value.set(0)
        
        # Rating Scale
        self.rating_scale = tk.Scale(self.search_frame, from_=0, to=10, tickinterval=1, orient='horizontal', length=150)
        self.rating_scale.config(state='disabled')

        ### Positions
        self.genre_dropdown.pack(side='left', expand=True)
        self.api_year_combo.pack(side='left', expand=True)
        rating_chkbtn.pack(side='left', expand=True)
        self.rating_scale.pack(side='left', expand=True)    
        
    def content_fill_home(self):
        '''
        Fill the content frame with the widgets associated with the Home button after clearing the frame:
        Top row = Current popular movies from api call
        Mid row = Upcoming releases from api call
        Bottom row = random selection of movies to watch from database
        '''
        for widget in self.content_frame.winfo_children():
            widget.grid_forget()
        
        # start=time.time()
        if not self.home_already_run:
            # Run once at start, then skip
            pop_list = self.api_obj.popularList()
            release_list = self.api_obj.releasedList()
            
            self.popular_frame = HomeRow(self.content_frame, B_WIDTH, C_HEIGHT, pop_list, self.api_obj, self.db_obj)
            self.upcoming_frame = HomeRow(self.content_frame, B_WIDTH, C_HEIGHT, release_list, self.api_obj, self.db_obj)
            
            self.p_label = tk.Label(self.content_frame, text="Popular Movies", font=16, justify='center')
            self.u_label = tk.Label(self.content_frame, text="Upcoming Movies", font=16, justify='center')
            self.r_label = tk.Label(self.content_frame, text="Random Movies to be watched", font=16, justify='center')
            
        random_list = self.db_obj.randomChoice()
        random_frame = HomeRow(self.content_frame, B_WIDTH, C_HEIGHT, random_list, self.api_obj, self.db_obj)
        # print("~*~*~*~*~*~*~*~ fill home took: {:.2f}s ~*~*~*~*~*~*~*~".format(time.time() - start))
        
        self.p_label.grid()
        self.popular_frame.grid(pady=(0,15))
        self.u_label.grid()
        self.upcoming_frame.grid(pady=(0,15))
        self.r_label.grid()
        random_frame.grid()
        
        self.home_already_run = True
        
    def content_fill_from_db(self, watched=None):
        '''
        Fill the content frame with a scrollable table of movies from the database.
        Params:
        watched - determines which query to use
        
        Calls MovieTable to create the frame.
        '''
        for widget in self.content_frame.winfo_children():
            widget.grid_forget()
            
        if watched:
            movie_list = self.db_obj.watchedList()
        else:
            movie_list = self.db_obj.wantToWatch()
            
        table = MovieTable(self.content_frame, B_WIDTH, C_HEIGHT, movie_list, self.api_obj, self.db_obj)
        
        table.grid()        
 
    def create_search(self, event=None, s_type=None):
        '''
        API search using by name or by detail methods from the backend.
        Params:
        event = optional parameter to allow call by event bind
        s_type = int used to deremine which API call to use, the return of a radiobutton control variable
        
        After api calls, content frame is cleared before new frame from MovieTable is put in.
        '''
        if s_type == 1:
            name = self.movie_name.get()
            if name == self.default_mn_text:
                return
            movie_list = self.api_obj.searchName(name)
        if s_type == 2:
            genre = '*'
            y= '*'
            rating = '*'
            
            if self.genre_value.get() != self.genres[0]: genre = self.genre_dict[self.genre_value.get()]
            if self.api_year_combo.current() != self.years[0]: y = self.years[self.api_year_combo.current()]
            if self.chkbtn_value.get() == 1: rating = self.rating_scale.get()
            
            print("Genre:", genre)
            print("Year :", y)
            print("rating:", rating)

            movie_list = self.api_obj.searchMovie(year=y, with_genres=genre, vote_average=rating)
            
        for widget in self.content_frame.winfo_children():
            widget.grid_forget()        
            
        table = MovieTable(self.content_frame, B_WIDTH, C_HEIGHT, movie_list, self.api_obj, self.db_obj)
        
        table.grid()
        
    def clear_entry(self, event):
        '''
        Clears Entry textbox on click event and text is the default text
        '''
        if self.movie_name.get() == self.default_mn_text:
            self.api_name_entry.delete(0,tk.END)

    def check_name(self, event):
        '''
        Refills Entry textbox on click event and StringVar is empty
        '''        
        if not self.movie_name.get():
            self.movie_name.set(self.default_mn_text)
            
    def scale_on_off(self):
        '''
        Enables/disables scale depending on checkbutton value
        '''
        if self.chkbtn_value.get() == 0:
            self.rating_scale.config(state='disabled')
            self.chkbtn_text.set("Rating Scale Disabled")
        else:
            self.rating_scale.config(state='active')
            self.chkbtn_text.set("Rating Scale Enabled")
    

    
    def user_profile(self):
        '''
        Looks to see if user profile data already exists,
        else calls GetUser to have user pick username and an avatar
        Saves generated data in a nested folder for access on subsequent application runs
        '''
        user_dir_name = ".user_profile"
        user_name_file = "username.txt"
        a_name = "user_avatar.png"
        # check for user directory
        user_dir = os.path.join(os.getcwd(), user_dir_name)
        if not os.path.isdir(user_dir):
            os.mkdir(user_dir_name)
        # check for username file
        name_file = os.path.join(os.getcwd(), user_dir_name, user_name_file)
        avatar_file = os.path.join(os.getcwd(), user_dir_name, a_name)
        if not (os.path.isfile(name_file) and os.path.isfile(avatar_file)):
            g = GetUser(self, user_dir_name, user_name_file)
            self.wait_window(g)
            if g.exit():
                sys.exit()
            
            un = g.get_username()
            with open(name_file,'w') as fh:
                fh.write(un)
                
            avatar_path = g.get_avatar_path()
            ext = avatar_path.split('.')
            save_path = f"{os.path.join(user_dir, a_name)}"
            shutil.copy(avatar_path,save_path)
        else:
            with open(name_file, 'r') as fh:
                un = fh.readline()
            for thing in os.listdir(user_dir):
                if a_name in thing:
                    avatar_path = os.path.join(user_dir, thing)
        return un, avatar_path
    
    def get_objs(self):
        return self.api_obj, self.db_obj

            
class GetUser(tk.Toplevel):
    '''
    Create a new Toplevel frame for user to enter a username and pick an avatar.
    If user tries to save data before both are done, a relavant error messagebox pops up.
    If user tries to close the window, they are warned it will close the program and given the option to cancel.
    Params:
    root - reference to root window
    dir_name = os path to directory where files should be stored
    file_name = user file to store username in
    '''
    def __init__(self, root, dir_name, file_name):
        super().__init__(root)
        self.grab_set()
        self.focus_set()
        self.transient(root)
        self.title("Set User Details")
        
        win_width = 240
        win_height = 150      
        # Gets both half the screen width/height and window width/height
        positionRight = int(self.winfo_screenwidth()/2 - win_width/2)
        positionDown = int(self.winfo_screenheight()/2.2 - win_height/2)
         
        # Positions the window in the center of the page.
        self.geometry(f"{win_width}x{win_height}+{positionRight}+{positionDown}")
        self.resizable(False,False)
        
        self.dir_name = dir_name
        self.file_name = file_name
        self.avatar = None
        self.avatar_file = None # path
        self.end = False
        
        ### Widgets
        main_label = ttk.Label(self, text="Input user name and select avatar")
        
        e_label= ttk.Label(self, text="Enter username")
        self.name = tk.StringVar()
        e = ttk.Entry(self, textvariable=self.name)

        b = ttk.Button(self, text="Select avatar", command=self.get_image)
        
        self.display_avatar = ttk.Label(self)
        
        save_btn = ttk.Button(self, text="Save choices", command=self.save_user)
        
        ### Grid
        main_label.grid(pady=5, columnspan=2)
        e_label.grid(row=1, column=0, padx=5)
        e.grid(row=1, column=1, padx=5)
        b.grid(row=2, column=0, padx=10)
        self.display_avatar.grid(row=2, column=1)
        save_btn.grid(row=3, columnspan=2, sticky='s')
        
        self.protocol('WM_DELETE_WINDOW', self.confirm)
        
    def get_image(self):
        '''
        Find an avatar image to represent the user
        Convert it to a resized tk PhotoImage
        '''
        avatars_folder = "Avatars"
        p = os.path.join(os.getcwd(), avatars_folder)
        if not os.path.isdir(p):
            tkmb.showerror("Error", f"Could not find folder: {avatars_folder} in current directory.", parent=self)
            sys.exit()
        self.avatar_file = tk.filedialog.askopenfilename(initialdir=p)
        
        avatar_image = Image.open(self.avatar_file)
        avatar_image = avatar_image.resize((50,50), Image.ANTIALIAS)
        self.avatar = ImageTk.PhotoImage(avatar_image)
        self.display_avatar['image'] = self.avatar
        
    def save_user(self):
        '''
        Validate user choices before destroying the window
        '''
        if not self.name.get():
            tkmb.showerror("Enter username", "Please enter a username. Do not leave blank.", parent=self)
            return
        if not self.avatar_file:
            tkmb.showerror("Select avatar", "Please select an avatar.", parent=self)
            return
        self.destroy()
        
    def get_username(self):
        return self.name.get()
        
    def get_avatar_path(self):
        return self.avatar_file
    
    def confirm(self):
        '''
        Notify root window that user wishes to exit early
        '''
        e = tkmb.askokcancel("Exit","Are you sure you wish to exit?")
        if e:
            self.destroy()
            self.end = True
            
    def exit(self):
        return self.end
    
    
class HomeRow(tk.Frame):
    '''
    Create frame of scrollable row of movies based on passed in movie list
    Params:
    root - reference to root window
    w = width to use for canvas
    h = base height to use for canvas sizing
    movie_list = formated list of tuples, each tuple being a container of movie data
    
    Designed by Maria, modified by Ben
    '''
    def __init__(self, root, w, h, movie_list, api_obj, db_obj):
        super().__init__(root)
        
        self.api_obj, self.db_obj = api_obj, db_obj
        
        self.canvas = tk.Canvas(self, width=w, height=(h//4), borderwidth=0)
        scrollbar1 = tk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=scrollbar1.set)
        self.frame = tk.Frame(self.canvas)
        
        self.canvas.pack(fill='x')
        scrollbar1.pack(fill='x')
        self.canvas.create_window((1,1), window=self.frame, anchor='nw')
        
        self.frame.bind("<Configure>", self.onFrameConfigure)
        threads = []

        #####################################################################
        # LEGIT, THIS CAN FAIL BECAUSE CPU ISN'T POWERFUL ENOUGH AND YOU GET:
        # RuntimeError: main thread is not in main loop
        #####################################################################
        for i, movie_tuple in enumerate(movie_list):
            t = threading.Thread(target=self.grid_movie, args=(i, movie_tuple,))
            threads.append(t)
            t.start()
            
    def grid_movie(self, i, movie_tuple):
        '''
        Method to allow threading to quickly create tk Buttons to place the movie poster and name
        Params:
        i = incrememntal grid column position
        movie_tuple = Movie data
        '''
        ## id, title, plot, genre_ids, avg_rating, poster
        # print(movie_tuple[1])
        movie_id = movie_tuple[0]
        render = ImageTk.PhotoImage(Image.open(BytesIO(movie_tuple[-1])).resize((83, 120), Image.ANTIALIAS))
        img = tk.Label(self, text=movie_tuple[1], image=render, compound='top')
        img.image = render
        b = tk.Button(self.frame, text=movie_tuple[1], wraplength=140, width=150, image=img.image, compound='top', height=150, justify=tk.CENTER)
        b.config(command=lambda:self.button_press(movie_id))
        b.grid(row=0, column=i, padx=10, pady=5)
        
    def button_press(self, movie_id):
        m = MovieInfo(self, movie_id, self.api_obj, self.db_obj)
        self.wait_window(m)   

    def onFrameConfigure(self, event):
        '''
        Reset the scroll region to encompass the frame window in the canvas
        '''
        self.canvas.configure(scrollregion=self.canvas.bbox("all")) 
        

class MovieTable(tk.Frame):
    '''
    Frames to display table of movie posters and names
    Params:
    root - reference to root window
    w = width to use for canvas
    h = base height to use for canvas sizing
    movie_list = formated list of tuples, each tuple being a container of movie data
    
    Designed by Maria, modified by Ben
    '''
    def __init__(self, root, w, h, movie_list, api_obj, db_obj):
        super().__init__(root)
        
        self.api_obj, self.db_obj = api_obj, db_obj
        
        self.canvas = tk.Canvas(self, width=w-25, height=h, borderwidth=0)
        scrollbar1 = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar1.set)
        frame2 = tk.Frame(self.canvas)
        
        self.canvas.pack(side='left',fill='y')
        scrollbar1.pack(side='right',fill='y')
        self.canvas.create_window((1,1), window=frame2, anchor='nw')
        
        frame2.bind("<Configure>", self.onFrameConfigure)
        
        wantToWatch = movie_list

        for row in range(math.ceil(len(wantToWatch) / 5)):
            num_col = 5
            if len(wantToWatch) < 5:
                num_col = len(wantToWatch)

            for column in range(num_col):
                #this try catches if the last row is not complete, breaks the loop
                try:
                    movie = wantToWatch[row * num_col + column]
                    movie_id = movie[0]
                    # print(row * num_col + column)
                    # print(wantToWatch[row * num_col + column][1])
                    render = ImageTk.PhotoImage(Image.open(BytesIO(movie[-1])).resize((125, 180), Image.ANTIALIAS))
                    img = tk.Label(self, text=movie[1], image=render, compound='top')
                    img.image = render
                    b = tk.Button(frame2, text=movie[1], wraplength=140, image=img.image, compound='top', width=150,
                              height=240, justify=tk.CENTER)
                    b.config(command=lambda i=movie_id:self.button_press(i))
                    b.grid(row=row, column=column, padx=20, pady=20)
                except IndexError:
                    break
                
    def button_press(self, movie_id):
        m = MovieInfo(self, movie_id, self.api_obj, self.db_obj)
        self.wait_window(m)    

    def onFrameConfigure(self, event):
        '''
        Reset the scroll region to encompass the frame window in the canvas
        '''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))    


class MovieInfo(tk.Toplevel):
    '''
    Top Level to display individual movie data
    Params:
    root - reference to root window
    movie_id = tmdb id of 1 movie
    api_obj = reference to instance of APITalker class from backend
    db_obj = reference to instance of DBTalker class from backend
    
    Designed by Maria, modified by Ben
    '''    
    def __init__(self, root, movie_id, api_obj, db_obj):
        super().__init__(root)

        self.geometry("600x500")

        self.myapi, self.mydb = api_obj, db_obj
        
        self.genre_dict = {t[0]:t[1] for t in self.mydb.getGenres()}
        ## {ID : Genre}
        
        if not self.mydb.selectOne(movie_id):
            movie = self.myapi.searchID(movie_id)
        else:
            movie = self.mydb.selectOne(movie_id)

        frame = tk.Frame(self)

        frame1 = tk.Frame(frame)
        render = ImageTk.PhotoImage(Image.open(BytesIO(movie[-1])).resize((280, 350), Image.ANTIALIAS))
        img = tk.Label(frame1, image=render, anchor='w')
        img.image = render
        img.pack()
        frame1.grid(row=0, column=0)
        frame2 = tk.Frame(frame)
        tk.Label(frame2, text=self.printText(movie), justify='left', wraplength=200).pack()
        frame2.grid(row=0, column=1)

        frame.pack()

        #762
        #movie_id # = 123
        frame3 = tk.Frame(self)
        f3 = tk.Frame(frame3)
        if not self.mydb.selectOne(movie_id):
            f1 = tk.Frame(frame3)
            f2 = tk.Frame(frame3)
        else:
            f2 = tk.Frame(frame3)
            f1 = tk.Frame(frame3)


        for frame in (f3, f2, f1):
            frame.grid(row=0, column=0, sticky='news')

        tk.Button(f1, text="Add to watched", width=15, command = lambda: [self.mydb.change_watched(movie[0]), self.raise_frame(f3)]).pack(side=tk.LEFT)
        tk.Button(f1, text="Remove from your list", width=15, command = lambda: [self.mydb.remove(movie[0]), self.raise_frame(f2)]).pack(side=tk.LEFT)
        tk.Button(f2, text="Add to watch list", width=15, command = lambda: [self.mydb.insert(movie), self.raise_frame(f1)]).pack(side=tk.LEFT)
        tk.Button(f3, text="Nothing to do here", width=15, command= self.destroy).pack(side=tk.LEFT)
        frame3.pack()
        
    def printText(self, movie):
        gids = movie[4].split(' ')
        genres = [self.genre_dict[int(gid)] for gid in gids]
        
        return f"{movie[1]}\n" \
               f"\n{movie[2]}\n" \
               f"\nGenre{'s' if len(genres) > 1 else ''}: {', '.join(genres)}\n" \
               f"\nRating: {movie[5]}\n" \
               f"\nYear: {movie[6]}"

    def raise_frame(self, frame):
        frame.tkraise()

if __name__ == '__main__':
    root = RootWindow()
    root.mainloop()