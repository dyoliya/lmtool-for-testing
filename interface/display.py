import os
import customtkinter as ctk
import threading
import webbrowser
import dropbox
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from customtkinter import filedialog
from tools.text_inactive_tool.text_inactive import main as run_text_inactive
from tools.phone_cleanup_tool.clean_up import main as run_clean_up
from tools.pipedrive_automation_tool.pipedrive_automation import main as run_automation
from tools.autodialer_cleanup_tool.cleanup_autodialer import main as run_autodialer
from tools.missing_deals_tool.missing_deals import main as run_missing_deals
from tools.missing_deals_tool.lookup import main as run_missing_deals_lookup
from tools.marketing_cleanup_tool.marketing_clean_up import main as run_marketing_cleanup
from tools.autodialer_cleanup_tool.cleaner_file_automation import dropbox_authentication
from tools.autodialer_cleanup_tool.cleaner_file_automation import main as update_list_cleaner_file
from tools.well_matching_tool.well_name_matching import main as run_well_matching_tool
from tools.c3_automation_tool.c3_automation import main as run_c3_tool
from tools.name_parsing_tool.name_parsing import main as run_name_parsing


# Outside function that will center a new pop up window relative to the main window
def center_new_window(main_window: ctk.CTkFrame,
                      new_window: ctk.CTkFrame) -> None:

    # Set the geomtry of the new window
    def set_geometry() -> None:

        # Get x and y position of the main window
        main_x = main_window.winfo_rootx()
        main_y = main_window.winfo_rooty()

        # Main window dimensions
        main_width = 1000
        main_height = 650

        # Update idle task to avoid bugs in changing geometry
        new_window.update_idletasks()

        # Get the new window dimensions
        new_window_width = new_window.winfo_width()
        new_window_height = new_window.winfo_height()

        # Calculate new the position of the new window so that it is centered
        x = main_x + (main_width - new_window_width) // 2
        y = main_y + (main_height - new_window_height) // 2

        # Apply new position
        new_window.geometry(f"{new_window_width}x{new_window_height}+{int(x)}+{int(y)}")

    # Add delay to avoid bugs in setting new window position
    new_window.after(70, set_geometry)

def center_main_window(screen: ctk.CTkFrame, width: int, height: int) -> str:

    # Get width and height of main window
    screen_width = screen.winfo_screenwidth()
    screen_height = screen.winfo_screenheight()

    # Calculate position to center window
    x = int((screen_width/2) - (width/2))
    y = int((screen_height/2) - (height/1.5))

    return f"{width}x{height}+{x}+{y}"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ########################
        #                      #
        #   MAIN APP WINDOW    #
        #                      #
        ########################

        # Configure window
        self.title("Lead Management Tools")
        self.geometry(center_main_window(self, 1000, 650))
        self.resizable(False, False)

        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left side frame
        self.left_side_frame = ctk.CTkFrame(self)
        self.left_side_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.left_side_frame.grid_columnconfigure(0, weight=1)
        self.left_side_frame.grid_rowconfigure(0, weight=1)

        # Tool Options Frame
        self.tool_options_frame = ctk.CTkScrollableFrame(self.left_side_frame)
        self.tool_options_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.tool_options_frame.grid_columnconfigure(0, weight=1)

        # Tool Window
        self.tool_window_frame = ctk.CTkFrame(self)
        self.tool_window_frame.grid_rowconfigure(0, weight=1)
        self.tool_window_frame.grid_columnconfigure(0, weight=1)
        self.tool_window_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        # Select from the tool buttons label
        self.tool_options_label = ctk.CTkLabel(self.tool_options_frame,
                                               text='Select a tool',
                                               font=ctk.CTkFont(
                                                   size=24,
                                                   weight='bold'
                                               ))
        self.tool_options_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')


        self.documentation_button = ctk.CTkButton(self.left_side_frame,
                                                     text='Official Documentation',
                                                     command=self.open_link,
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343',
                                                     font=ctk.CTkFont(
                                                         weight='bold'
                                                     ))
        self.documentation_button.grid(row=1, column=0, padx=10, pady=(0,10), stick='nsew')

        self.clean_phone_tool_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='Phone Cleaning Tool',
                                                     command=self.display_phone_clean_tool,
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.clean_phone_tool_button.grid(row=1, column=0, padx=10, pady=5, sticky='nsew')
        self.clean_phone_tool_button.bind("<Button-1>", lambda event: self.track_button_click(1))

        self.text_inactive_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='Text Inactive Tool',
                                                     command=lambda:self.show_frame(TextInactive),
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.text_inactive_button.grid(row=2, column=0, padx=10, pady=5, sticky='nsew')
        self.text_inactive_button.bind("<Button-1>", lambda event: self.track_button_click(2))

        self.pipedrive_automation_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='Pipedrive Automation Tool',
                                                     command=lambda:self.show_frame(PipedriveAutomation),
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.pipedrive_automation_button.grid(row=3, column=0, padx=10, pady=5, sticky='nsew')
        self.pipedrive_automation_button.bind("<Button-1>", lambda event: self.track_button_click(3))

        self.autodialer_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='AutoDialer Cleanup Tool',
                                                     command=lambda:self.show_frame(AutoDialerCleaner),
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.autodialer_button.grid(row=4, column=0, padx=10, pady=5, sticky='nsew')
        self.autodialer_button.bind("<Button-1>", lambda event: self.track_button_click(4))

        self.missing_deals_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='Missing Deals Text Tool',
                                                     command=lambda:self.show_frame(MissingDealsText),
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.missing_deals_button.grid(row=5, column=0, padx=10, pady=5, sticky='nsew')
        self.missing_deals_button.bind("<Button-1>", lambda event: self.track_button_click(5))

        self.marketing_cleanup_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='Marketing Cleanup Tool',
                                                     command=lambda:self.show_frame(MarketingCleanupTool),
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.marketing_cleanup_button.grid(row=6, column=0, padx=10, pady=5, sticky='nsew')
        self.marketing_cleanup_button.bind("<Button-1>", lambda event: self.track_button_click(6))

        self.well_matching_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='Well Matching Tool',
                                                     command=lambda:self.show_frame(WellMatchingTool),
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.well_matching_button.grid(row=7, column=0, padx=10, pady=5, sticky='nsew')
        self.well_matching_button.bind("<Button-1>", lambda event: self.track_button_click(7))

        self.c3_automation_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='C3 Automation Tool',
                                                     command=lambda:self.show_frame(C3AutomationTool),
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.c3_automation_button.grid(row=8, column=0, padx=10, pady=5, sticky='nsew')
        self.c3_automation_button.bind("<Button-1>", lambda event: self.track_button_click(8))

        self.c3_automation_button = ctk.CTkButton(self.tool_options_frame,
                                                     text='Name Parsing Tool',
                                                     command=lambda:self.show_frame(NameParsingTool),
                                                     fg_color='#5b5c5c',
                                                     hover_color='#424343')
        self.c3_automation_button.grid(row=9, column=0, padx=10, pady=5, sticky='nsew')
        self.c3_automation_button.bind("<Button-1>", lambda event: self.track_button_click(9))

        self.clicked_button_id = ctk.IntVar()
        self.current_frame = None
        self.input_file_check, self.save_path_check = False, False
        self.APP_KEY = os.getenv('DROPBOX_APP_KEY')
        self.APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
        self.show_frame(InitialFrame)

    ##################
    #                #
    # HELPER METHODS #
    #                #
    ##################

    def display_checklist(self, window):
        
        # Function to check if all checkboxes are checked
        def check_all_selected():
            if all(state.get() for state in checkbox_states):
                confirm_button.configure(state="normal", fg_color='#5b5c5c')
            else:
                confirm_button.configure(state="disabled", fg_color='#424343')

        window.destroy()

        checklist_window = ctk.CTkToplevel()
        center_new_window(self, checklist_window)
        checklist_window.resizable(False, False)
        checklist_window.geometry("470x400")
        checklist_window.grid_columnconfigure(0, weight=1)
        checklist_window.grid_rowconfigure(0, weight=1)
        checklist_window.attributes('-topmost', True)
        checklist_window.protocol("WM_DELETE_WINDOW", lambda: None)
        checklist_window.title("Output Checklist")
        checklist_window.grid_rowconfigure(1, weight=1)
        checklist_window.grid_columnconfigure(0, weight=1)
        checklist_scrollable_frame = ctk.CTkScrollableFrame(checklist_window,
                                                            corner_radius=20)
        checklist_scrollable_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew", ipadx=5, ipady=5)

        checkbox_states = []
        output_checklist_dict = {
            1 : ["Correct output column names",
                 "No Duplicates in phone_number column",
                 "Correctness of tagging per lead from\ncolumn reason_for_removal",
                 "If tagged 'in_pipedrive is Y', verify if value in column\nin_pipedrive is Y from input file",
                 "If tagged 'rc_pd is Yes', verify if value in column\n rc_pd is Yes from input file",
                 "If tagged 'Both type & carrier_type are Landline', verify\nif both columns type & carrier_type are Landline from input file",
                 "If tagged 'text_opt_in is No', verify if column text_opt_in\nis No from input file",
                 "If tagged 'contact_deal_id Not Empty', verify if column\ncontact_deal_id is empty from input file",
                 "If tagged 'contact_deal_status Not Empty', verify if column\ncontact_deal_status is empty from input file",
                 "If tagged 'contact_person_id Not Empty', verify if column\ncontact_person_id is empty from input file",
                 "If tagged 'phone_number_deal_id Not Empty', verify if column\nphone_number_deal_id is empty from input file",
                 "If tagged 'phone_number_deal_status Not Empty', verify if\ncolumn phone_number_deal_status is empty from input file",
                 "If tagged 'RVM - Last RVM Date - last 7 days from tool run\ndate', verify if the date from column RVM - Last RVM Date is\n7 days ago from today from input file",
                 "If tagged 'Latest Text Marketing Date (Sent) - last 7 days\nfrom tool run date', verify if the date from column Latest\nText Marketing Date (Sent) is 7 days ago from today from input file",
                 "If tagged 'Rolling 30 Days Rvm Count and Rolling 30 Days\nText Marketing Count - total >= 3', verify if the total count\nof columns Rolling 30 Days Rvm Count and Rolling 30 Days Text\nMarketing Count is less than or equal to 3 from input file",
                 "If tagged 'Deal - ID Not Empty', verify if column\nDeal - ID is empty from input file",
                 "If tagged 'Deal - Text Opt-in is No', verify if column\nDeal - Text Opt-in is No from input file",
                 "For leads with empty reason_for_removal values, verify\nif all of the previous column conditions are not satisfied",
                 'Multiple tagging for reason_for_removal\nwith separator of " , "',
                 "Output file name and format"
                 ],
            
            2: [
                "Correct output column names",
                "Two output files if tool created new deals\n(FU and New Deals)",
                "No blank values for column Deal ID in FU file",
                'Multiple Deal IDs in FU file with separator of " | "',
                '"Text Inactive - For Review" value in Deal - Label column',
                "Proper row value and format in columns Deal - Title,\nDeal - Deal Summary, Person - Name and Note (if any)",
                "Person - Phone, Person - Phone 1 not blank",
                "Importing of output files to Pipedrive is successful"
                ],
            
            3: [
                "Correct output column names",
                "No duplicate values from column Deal - ID",
                "Only unique serial numbers from column Deal - Serial Number",
                "Deal - Deal Summary value should be 'Completed'",
                "Proper formatting of values from column\nPerson - Mailing Address (should have '..., USA' at the end)",
                "For non-empty values from columns 'Person - Email' and\n'Person - Phone', verify if the same values are reflected for\ncolumns 'Person - Email 1' and 'Person - Phone 1' respectively"
                ],
            
            4: [
                "AutoDialer List"
               ],

            5: [
                "Missing Deals Text List"
               ],
            
            6: [
                "Marketing Cleanup Tool List"
               ],
            
            7: [
                "Well Matching Tool List"
               ],
            
            8: [
                "C3 Automation Tool List"
               ],

            8: [
                "Name Parsing Tool List"
               ]
        }
        checkbox_labels = output_checklist_dict[self.clicked_button_id.get()]

        checklist_label = ctk.CTkLabel(checklist_window,
                                       text="Verify the following from the output file(s)",
                                       font=ctk.CTkFont(
                                           size=18,
                                           weight='bold'
                                       ))
        checklist_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Create checkboxes for each item in the list
        for label in checkbox_labels:
            state = ctk.BooleanVar()
            checkbox = ctk.CTkCheckBox(checklist_scrollable_frame,
                                       text=label,
                                       variable=state,
                                       fg_color='green',
                                       hover_color='green',
                                       command=check_all_selected)
            checkbox.pack(pady=5, anchor='w')
            checkbox_states.append(state)
        
        confirm_button = ctk.CTkButton(checklist_window,
                                       text="Confirm",
                                       state="disabled",
                                       fg_color='#424343',
                                       hover_color='#424343',
                                       command=checklist_window.destroy)
        confirm_button.grid(row=2, column=0, padx=5, pady=(5,10))

    def track_button_click(self, button_id):
        self.clicked_button_id.set(button_id)

    def show_frame(self, frame_class):
        """Destroys the current frame and replaces it with a new one."""
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_class(self.tool_window_frame, self)

    
    def open_link(self):
        webbrowser.open("https://github.com/armielgonzzz/universal-tool/blob/main/README.md")
    
    ##############################
    #                            #
    # PHONE NUMBER CLEAN UP TOOL #
    #                            #
    ##############################

    def get_latest_update(self, auth_code):

        auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(self.APP_KEY, self.APP_SECRET)   
        oauth_result = auth_flow.finish(auth_code)
        if oauth_result.access_token:
            self.auth_code = oauth_result.access_token
            dbx = dropbox.Dropbox(oauth_result.access_token)
            metadata = dbx.files_get_metadata('/List Cleaner & JC DNC/DNC (Cold-PD).csv')
            last_modified_date = metadata.client_modified
            utc_time = last_modified_date.replace(tzinfo=ZoneInfo("UTC"))
            cst_time = utc_time.astimezone(ZoneInfo("America/Chicago"))
            self.last_update_label.configure(text=f'List cleaner file last update: {cst_time.strftime("%Y-%m-%d %H:%M:%S %Z")}')
    
    def authentication_result_window(self):
        authentication_result = ctk.CTkToplevel()
        authentication_result.resizable(False, False)
        authentication_result.geometry("400x200")
        authentication_result.grid_rowconfigure(0, weight=1)
        authentication_result.grid_columnconfigure(0, weight=1)
        authentication_result.attributes('-topmost', True)
        authentication_result.title("Run Tool")

        tool_run_label = ctk.CTkLabel(authentication_result,
                                      text="SUCCESSFULLY Authenticated Dropbox Code" if self.auth_code else "Authentication FAILED",
                                      wraplength=300,
                                      font=ctk.CTkFont(
                                          size=14,
                                          weight='normal'))
        tool_run_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="nsew")
        tool_run_button = ctk.CTkButton(authentication_result,
                                        text="OK",
                                        fg_color='#5b5c5c',
                                        hover_color='#424343',
                                        command=lambda:authentication_result.destroy())
        tool_run_button.grid(row=1, column=0, padx=10, pady=(5, 15))


    def authenticate_dropbox(self, tool_window, func):
        def submit_action(window, tool_window, func):
            user_input = input_field.get()
            if user_input:
                self.user_input = user_input
                self.get_latest_update(self.user_input)
                window.destroy()
                self.authentication_result_window()
                if self.input_file_check and self.save_path_check and self.auth_code:
                    switch_frame = ctk.CTkFrame(tool_window, fg_color="transparent")
                    switch_frame.grid(row=7, column=0, padx=5, sticky="nsew")
                    switch_frame.grid_rowconfigure(0, weight=1)
                    switch_frame.grid_columnconfigure((0,1,2,3), weight=1)
                    selected_mode = ctk.StringVar(value="call_marketing")

                    mode_label = ctk.CTkLabel(switch_frame,
                                            text="Select run mode: ")
                    mode_label.grid(row=0, column=0, padx=5, sticky="nsew")

                    # Left radio button
                    radio_off = ctk.CTkRadioButton(switch_frame, text="Call Marketing", variable=selected_mode, value="call_marketing")
                    radio_off.grid(row=0, column=1, padx=5, sticky="nsew")

                    # Right radio button
                    radio_on = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Raw Cleaning", variable=selected_mode, value="text_marketing")
                    radio_on.grid(row=0, column=2, padx=5, sticky="nsew")

                    recleaning_button = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Re-cleaning", variable=selected_mode, value="recleaning")
                    recleaning_button.grid(row=0, column=3, padx=5, sticky="nsew")

                    run_tool_button = ctk.CTkButton(tool_window,
                                                    text='RUN TOOL',
                                                    command=lambda: self.trigger_tool(func, self.auth_code, self.file_paths, self.save_path, selected_mode.get()),
                                                    height=36,
                                                    width=240,
                                                    fg_color='#d99125',
                                                    hover_color='#ae741e',
                                                    text_color='#141414',
                                                    corner_radius=50,
                                                    font=ctk.CTkFont(
                                                        size=18,
                                                        weight='bold'
                                                    ))
                    run_tool_button.grid(row=8, column=0, padx=10, pady=5)

        # Create the authentication frame (a new top-level window)
        authentication_frame = ctk.CTkToplevel(self)
        authentication_frame.resizable(False, False)
        authentication_frame.geometry("470x180")
        authentication_frame.grid_columnconfigure(0, weight=1)
        authentication_frame.grid_rowconfigure((2), weight=1)  # Adjust grid row configuration
        authentication_frame.attributes('-topmost', True)
        authentication_frame.title("Dropbox Authentication")

        # Button to open authentication link
        open_link = ctk.CTkButton(authentication_frame,
                                text="Open Authentication Link",
                                fg_color='#5b5c5c',
                                hover_color='#424343',
                                command=lambda: dropbox_authentication())
        open_link.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        input_field = ctk.CTkEntry(authentication_frame, placeholder_text="Enter the value here")
        input_field.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        submit_button = ctk.CTkButton(authentication_frame,
                                      text="Submit",
                                      fg_color='#d99125',
                                      hover_color='#ae741e',
                                      text_color='#141414',
                                      corner_radius=50,
                                      font=ctk.CTkFont(size=18, weight='bold'),
                                      command=lambda: submit_action(authentication_frame, tool_window, func))
        submit_button.grid(row=2, column=0, padx=10, pady=20, sticky='nsew')

    def display_phone_clean_tool(self):

        self.input_file_check, self.save_path_check, self.cleaner_file_check = False, False, False
        self.auth_code = None
        self.user_input = None

        self.current_frame = ctk.CTkFrame(self.tool_window_frame)
        self.current_frame.grid_rowconfigure((7,8), weight=1)
        self.current_frame.grid_columnconfigure(0, weight=1)
        self.current_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        label = ctk.CTkLabel(self.current_frame,
                             text="Phone Cleaning Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        update_cleaner_button = ctk.CTkButton(self.current_frame,
                                              text="Authenticate Dropbox",
                                              fg_color='#5b5c5c',
                                              hover_color='#424343',
                                              command=lambda:self.authenticate_dropbox(self.current_frame, run_clean_up))
        update_cleaner_button.grid(row=1, column=0, padx=5, pady=5, sticky="ns")
        
        select_file_button = ctk.CTkButton(self.current_frame,
                                           text='Select files to process',
                                           command=lambda: self.open_select_file(frame=self.current_frame, func=run_clean_up),
                                           fg_color='#5b5c5c',
                                           hover_color='#424343')
        select_file_button.grid(row=3, column=0, padx=10, pady=5)

        define_save_path_button = ctk.CTkButton(self.current_frame,
                                                text='Save output files to',
                                                command=lambda: self.select_save_directory(frame=self.current_frame, func=run_clean_up),
                                                fg_color='#5b5c5c',
                                                hover_color='#424343')
        define_save_path_button.grid(row=5, column=0, padx=10, pady=5)

        self.last_update_label = ctk.CTkLabel(self.current_frame,
                                              text=None,
                                              fg_color='transparent')
        self.last_update_label.grid(row=9, column=0, padx=5, pady=5, sticky="nsew")


    def open_select_file(self, frame: ctk.CTkFrame, func):

        self.file_paths = filedialog.askopenfilenames(title="Select a file",
                                               filetypes=[("All Files", "*.*")])
        if self.file_paths:

            select_files_frame = ctk.CTkScrollableFrame(frame,height=100)
            select_files_frame.grid_columnconfigure(0, weight=1)
            select_files_frame.grid(row=4, column=0, padx=30, pady=5, sticky='nsew')

            for index, file in enumerate(self.file_paths):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(select_files_frame,
                                                text=file_name,
                                                wraplength=400)
                selected_files_label.grid(row=index, column=0, padx=10, pady=3, sticky='nsew')

            self.input_file_check = True

            if self.input_file_check and self.save_path_check and self.auth_code:
                switch_frame = ctk.CTkFrame(frame, fg_color="transparent")
                switch_frame.grid(row=7, column=0, padx=5, sticky="nsew")
                switch_frame.grid_rowconfigure(0, weight=1)
                switch_frame.grid_columnconfigure((0,1,2,3), weight=1)
                selected_mode = ctk.StringVar(value="call_marketing")

                mode_label = ctk.CTkLabel(switch_frame,
                                        text="Select run mode: ")
                mode_label.grid(row=0, column=0, padx=5, sticky="nsew")

                # Left radio button
                radio_off = ctk.CTkRadioButton(switch_frame, text="Call Marketing", variable=selected_mode, value="call_marketing")
                radio_off.grid(row=0, column=1, padx=5, sticky="nsew")

                # Right radio button
                radio_on = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Raw Cleaning", variable=selected_mode, value="text_marketing")
                radio_on.grid(row=0, column=2, padx=5, sticky="nsew")

                recleaning_button = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Re-cleaning", variable=selected_mode, value="recleaning")
                recleaning_button.grid(row=0, column=3, padx=5, sticky="nsew")

                run_tool_button = ctk.CTkButton(frame,
                                                text='RUN TOOL',
                                                command=lambda: self.trigger_tool(func, self.auth_code, self.file_paths, self.save_path, selected_mode.get()),
                                                height=36,
                                                width=240,
                                                fg_color='#d99125',
                                                hover_color='#ae741e',
                                                text_color='#141414',
                                                corner_radius=50,
                                                font=ctk.CTkFont(
                                                    size=18,
                                                    weight='bold'
                                                ))
                run_tool_button.grid(row=8, column=0, padx=10, pady=5)
    
    def select_save_directory(self, frame: ctk.CTkFrame, func):

        self.save_path = filedialog.askdirectory(title="Select save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(frame,
                                       text=None,
                                       corner_radius=10,
                                       fg_color='#292929',
                                       wraplength=400)
            save_path_label.grid(row=6, column=0, padx=30, pady=5, sticky='nsew', ipadx=8, ipady=8)

            save_path_label.configure(text=f"{self.save_path}")
            self.save_path_check = True

            if self.input_file_check and self.save_path_check and self.auth_code:
                switch_frame = ctk.CTkFrame(frame, fg_color="transparent")
                switch_frame.grid(row=7, column=0, padx=5, sticky="nsew")
                switch_frame.grid_rowconfigure(0, weight=1)
                switch_frame.grid_columnconfigure((0,1,2,3), weight=1)
                selected_mode = ctk.StringVar(value="call_marketing")

                mode_label = ctk.CTkLabel(switch_frame,
                                        text="Select run mode: ")
                mode_label.grid(row=0, column=0, padx=5, sticky="nsew")

                # Left radio button
                radio_off = ctk.CTkRadioButton(switch_frame, text="Call Marketing", variable=selected_mode, value="call_marketing")
                radio_off.grid(row=0, column=1, padx=5, sticky="nsew")

                # Right radio button
                radio_on = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Raw Cleaning", variable=selected_mode, value="text_marketing")
                radio_on.grid(row=0, column=2, padx=5, sticky="nsew")

                recleaning_button = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Re-cleaning", variable=selected_mode, value="recleaning")
                recleaning_button.grid(row=0, column=3, padx=5, sticky="nsew")

                run_tool_button = ctk.CTkButton(frame,
                                                text='RUN TOOL',
                                                command=lambda: self.trigger_tool(func, self.auth_code, self.file_paths, self.save_path, selected_mode.get()),
                                                height=36,
                                                width=240,
                                                fg_color='#d99125',
                                                hover_color='#ae741e',
                                                text_color='#141414',
                                                corner_radius=50,
                                                font=ctk.CTkFont(
                                                    size=18,
                                                    weight='bold'
                                                ))
                run_tool_button.grid(row=8, column=0, padx=10, pady=5)
    
    def select_list_cleaner_file(self, frame: ctk.CTkFrame, func):
        self.cleaner_file = filedialog.askopenfilename(title="Select list cleaner file",
                                                        filetypes=[("All Files", "*.*")])
        if self.cleaner_file:
            cleaner_file_label = ctk.CTkLabel(frame,
                                              text=f"{os.path.basename(self.cleaner_file)}",
                                              fg_color="transparent")
            cleaner_file_label.grid(row=2, column=0, padx=5, pady=5)
            self.cleaner_file_check = True
            if self.input_file_check and self.save_path_check and self.cleaner_file_check:
                switch_frame = ctk.CTkFrame(frame, fg_color="transparent")
                switch_frame.grid(row=7, column=0, padx=5, sticky="nsew")
                switch_frame.grid_rowconfigure(0, weight=1)
                switch_frame.grid_columnconfigure((0,1,2,3), weight=1)
                selected_mode = ctk.StringVar(value="call_marketing")

                mode_label = ctk.CTkLabel(switch_frame,
                                        text="Select run mode: ")
                mode_label.grid(row=0, column=0, padx=5, sticky="nsew")

                # Left radio button
                radio_off = ctk.CTkRadioButton(switch_frame, text="Call Marketing", variable=selected_mode, value="call_marketing")
                radio_off.grid(row=0, column=1, padx=5, sticky="nsew")

                # Right radio button
                radio_on = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Raw Cleaning", variable=selected_mode, value="text_marketing")
                radio_on.grid(row=0, column=2, padx=5, sticky="nsew")

                recleaning_button = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Re-cleaning", variable=selected_mode, value="recleaning")
                recleaning_button.grid(row=0, column=3, padx=5, sticky="nsew")

                run_tool_button = ctk.CTkButton(frame,
                                                text='RUN TOOL',
                                                command=lambda: self.trigger_tool(func, self.cleaner_file, self.file_paths, self.save_path, selected_mode.get()),
                                                height=36,
                                                width=240,
                                                fg_color='#d99125',
                                                hover_color='#ae741e',
                                                text_color='#141414',
                                                corner_radius=50,
                                                font=ctk.CTkFont(
                                                    size=18,
                                                    weight='bold'
                                                ))
                run_tool_button.grid(row=8, column=0, padx=10, pady=5)

    def tool_running_window(self):
        
        tool_run_window = ctk.CTkToplevel()
        center_new_window(self, tool_run_window)
        tool_run_window.resizable(False, False)
        tool_run_window.geometry("400x200")
        tool_run_window.grid_columnconfigure(0, weight=1)
        tool_run_window.grid_rowconfigure(0, weight=1)
        tool_run_window.attributes('-topmost', True)
        tool_run_window.title("Run Tool")

        tool_run_label = ctk.CTkLabel(tool_run_window,
                                      text="Tool is running in background.\nPlease wait for the tool to finish",
                                      font=ctk.CTkFont(
                                          size=16))
        tool_run_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        return tool_run_window
    
    def trigger_tool(self, func, *args, **kwargs):
        window = self.tool_running_window()
        threading.Thread(target=self.run_clean_up_with_callback, args=(window, func, *args), kwargs=kwargs).start()

    def run_clean_up_with_callback(self, window, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.tool_result(result=True)

        except:
            self.tool_result(result=False)
        
        finally:
            window.destroy()

    def tool_result(self, result: bool=False):

        tool_result_window = ctk.CTkToplevel()
        center_new_window(self, tool_result_window)
        tool_result_window.resizable(False, False)
        tool_result_window.geometry("400x200")
        tool_result_window.grid_rowconfigure(0, weight=1)
        tool_result_window.grid_columnconfigure(0, weight=1)
        tool_result_window.attributes('-topmost', True)
        tool_result_window.title("Run Tool")

        tool_run_label = ctk.CTkLabel(tool_result_window,
                                      text="SUCCESSFULLY processed all files" if result else "Tool run FAILED",
                                      wraplength=300,
                                      font=ctk.CTkFont(
                                          size=14,
                                          weight='normal'))
        tool_run_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="nsew")
        tool_run_button = ctk.CTkButton(tool_result_window,
                                        text="OK",
                                        fg_color='#5b5c5c',
                                        hover_color='#424343',
                                        command=lambda:
                                        self.display_checklist(tool_result_window) if result else tool_result_window.destroy())
        tool_run_button.grid(row=1, column=0, padx=10, pady=(5, 15))

class InitialFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        welcome_label = ctk.CTkLabel(self,
                                     text="Welcome to\nLead Management\nTools",
                                     font=ctk.CTkFont(
                                         size=36,
                                         weight='bold'))
        welcome_label.grid(row=0, column=0, padx=10, pady=10)


class TextInactive(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.controller.input_file_check = False
        self.controller.save_path_check = False
        self.files_to_process = False
        self.save_path = False
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        label = ctk.CTkLabel(self,
                             text="Text Inactive Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        
        select_file_button = ctk.CTkButton(self,
                                           text='Select files to process',
                                           command=lambda: self.select_files_to_clean(self),
                                           fg_color='#5b5c5c',
                                           hover_color='#424343')
        select_file_button.grid(row=1, column=0, padx=10, pady=5)

        define_save_path_button = ctk.CTkButton(self,
                                                text='Save output files to',
                                                command=lambda: self.select_save_path(self),
                                                fg_color='#5b5c5c',
                                                hover_color='#424343')
        define_save_path_button.grid(row=4, column=0, padx=10, pady=5)

    def select_files_to_clean(self, window):

        self.files_to_process = filedialog.askopenfilenames(title="Select files to clean",
                                                          filetypes=[("All Files", "*.*")])
        if self.files_to_process:
            files_to_clean_frame = ctk.CTkScrollableFrame(window,
                                                          height=80)
            files_to_clean_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
            files_to_clean_frame.grid_columnconfigure(0, weight=1)

            for i, file in enumerate(self.files_to_process):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(files_to_clean_frame,
                                                    text=file_name,
                                                    wraplength=400)
                selected_files_label.grid(row=i, column=0, padx=10, pady=3, sticky='nsew')       
            self.check_run()         
    
    def select_save_path(self, window):
        self.save_path = filedialog.askdirectory(title="Save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(window,
                                           text=f"{self.save_path}",
                                           fg_color="transparent",
                                           wraplength=400)
            save_path_label.grid(row=5, column=0, padx=5, pady=5)
            self.check_run()

    
    def check_run(self):
        if self.files_to_process and self.save_path:
            run_tool_button = ctk.CTkButton(self,
                                            text='RUN TOOL',
                                            height=36,
                                            width=240,
                                            fg_color='#d99125',
                                            hover_color='#ae741e',
                                            text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_text_inactive,
                                                                                        self.files_to_process,
                                                                                        self.save_path))
            run_tool_button.grid(row=6, column=0, padx=10, pady=5)

class PipedriveAutomation(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.controller.input_file_check = False
        self.controller.save_path_check = False
        self.files_to_process = False
        self.save_path = False
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        label = ctk.CTkLabel(self,
                             text="Pipedrive Automation Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        
        select_file_button = ctk.CTkButton(self,
                                           text='Select files to process',
                                           command=lambda: self.select_files_to_clean(self),
                                           fg_color='#5b5c5c',
                                           hover_color='#424343')
        select_file_button.grid(row=1, column=0, padx=10, pady=5)

        define_save_path_button = ctk.CTkButton(self,
                                                text='Save output files to',
                                                command=lambda: self.select_save_path(self),
                                                fg_color='#5b5c5c',
                                                hover_color='#424343')
        define_save_path_button.grid(row=4, column=0, padx=10, pady=5)

    def select_files_to_clean(self, window):

        self.files_to_process = filedialog.askopenfilenames(title="Select files to clean",
                                                          filetypes=[("All Files", "*.*")])
        if self.files_to_process:
            files_to_clean_frame = ctk.CTkScrollableFrame(window,
                                                          height=80)
            files_to_clean_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
            files_to_clean_frame.grid_columnconfigure(0, weight=1)

            for i, file in enumerate(self.files_to_process):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(files_to_clean_frame,
                                                    text=file_name,
                                                    wraplength=400)
                selected_files_label.grid(row=i, column=0, padx=10, pady=3, sticky='nsew')       
            self.check_run()         
    
    def select_save_path(self, window):
        self.save_path = filedialog.askdirectory(title="Save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(window,
                                           text=f"{self.save_path}",
                                           fg_color="transparent",
                                           wraplength=400)
            save_path_label.grid(row=5, column=0, padx=5, pady=5)
            self.check_run()

    
    def check_run(self):
        if self.files_to_process and self.save_path:
            run_tool_button = ctk.CTkButton(self,
                                            text='RUN TOOL',
                                            height=36,
                                            width=240,
                                            fg_color='#d99125',
                                            hover_color='#ae741e',
                                            text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_automation,
                                                                                        self.files_to_process,
                                                                                        self.save_path))
            run_tool_button.grid(row=6, column=0, padx=10, pady=5)

class AutoDialerCleaner(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        load_dotenv(dotenv_path='misc/.env')
        self.APP_KEY = os.getenv('DROPBOX_APP_KEY')
        self.APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
        self.controller = controller
        self.controller.input_file_check = False
        self.controller.save_path_check = False
        self.files_to_clean = False
        self.save_path = False
        self.auth_code = None
        self.user_input = None
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((7,8), weight=1)

        label = ctk.CTkLabel(self,
                             text="AutoDialer Cleanup Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=(10,0), sticky='nsew')

        authenticate_dropbox_button = ctk.CTkButton(self,
                                              text="Authenticate Dropbox",
                                              fg_color='#5b5c5c',
                                              hover_color='#424343',
                                              command=lambda:self.authenticate_dropbox(self))
        authenticate_dropbox_button.grid(row=1, column=0, padx=5, pady=5, sticky="ns")

        update_cleaner_button = ctk.CTkButton(self,
                                            text="Update list cleaner file",
                                            fg_color='#5b5c5c',
                                            hover_color='#424343',
                                            command=lambda:self.update_list_cleaner())
        update_cleaner_button.grid(row=2, column=0, padx=5, pady=5, sticky="ns")

        files_to_process_button = ctk.CTkButton(self,
                                    text="Select files to clean",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_files_to_clean(self))
        files_to_process_button.grid(row=3, column=0, padx=5, pady=5, sticky="ns")

        save_path_button = ctk.CTkButton(self,
                                    text="Save output files to",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_save_path(self))
        save_path_button.grid(row=5, column=0, padx=5, pady=5, sticky="ns")

        self.last_update_label = ctk.CTkLabel(self,
                                              text=None,
                                              fg_color='transparent')
        self.last_update_label.grid(row=9, column=0, padx=5, pady=5, sticky="nsew")

    def get_latest_update(self, auth_code):

        auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(self.APP_KEY, self.APP_SECRET)   
        oauth_result = auth_flow.finish(auth_code)
        if oauth_result.access_token:
            self.auth_code = oauth_result.access_token
            dbx = dropbox.Dropbox(oauth_result.access_token)
            metadata = dbx.files_get_metadata('/List Cleaner & JC DNC/DNC (Cold-PD).csv')
            last_modified_date = metadata.client_modified
            utc_time = last_modified_date.replace(tzinfo=ZoneInfo("UTC"))
            cst_time = utc_time.astimezone(ZoneInfo("America/Chicago"))
            self.last_update_label.configure(text=f'List cleaner file last update: {cst_time.strftime("%Y-%m-%d %H:%M:%S %Z")}')
    
    def authentication_result_window(self):
        authentication_result = ctk.CTkToplevel()
        authentication_result.resizable(False, False)
        authentication_result.geometry("400x200")
        authentication_result.grid_rowconfigure(0, weight=1)
        authentication_result.grid_columnconfigure(0, weight=1)
        authentication_result.attributes('-topmost', True)
        authentication_result.title("Run Tool")

        tool_run_label = ctk.CTkLabel(authentication_result,
                                      text="SUCCESSFULLY Authenticated Dropbox Code" if self.auth_code else "Authentication FAILED",
                                      wraplength=300,
                                      font=ctk.CTkFont(
                                          size=14,
                                          weight='normal'))
        tool_run_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="nsew")
        tool_run_button = ctk.CTkButton(authentication_result,
                                        text="OK",
                                        fg_color='#5b5c5c',
                                        hover_color='#424343',
                                        command=lambda:authentication_result.destroy())
        tool_run_button.grid(row=1, column=0, padx=10, pady=(5, 15))


    def authenticate_dropbox(self, tool_window):
        def submit_action(window, tool_window):
            user_input = input_field.get()
            if user_input:
                self.user_input = user_input
                self.get_latest_update(self.user_input)
                window.destroy()
                self.authentication_result_window()
                self.check_run()

        # Create the authentication frame (a new top-level window)
        authentication_frame = ctk.CTkToplevel(self)
        authentication_frame.resizable(False, False)
        authentication_frame.geometry("470x180")
        authentication_frame.grid_columnconfigure(0, weight=1)
        authentication_frame.grid_rowconfigure((2), weight=1)  # Adjust grid row configuration
        authentication_frame.attributes('-topmost', True)
        authentication_frame.title("Dropbox Authentication")

        # Button to open authentication link
        open_link = ctk.CTkButton(authentication_frame,
                                text="Open Authentication Link",
                                fg_color='#5b5c5c',
                                hover_color='#424343',
                                command=lambda: dropbox_authentication())
        open_link.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        input_field = ctk.CTkEntry(authentication_frame, placeholder_text="Enter the value here")
        input_field.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        submit_button = ctk.CTkButton(authentication_frame,
                                      text="Submit",
                                      fg_color='#d99125',
                                      hover_color='#ae741e',
                                      text_color='#141414',
                                      corner_radius=50,
                                      font=ctk.CTkFont(size=18, weight='bold'),
                                      command=lambda: submit_action(authentication_frame, tool_window))
        submit_button.grid(row=2, column=0, padx=10, pady=20, sticky='nsew')

    def select_files_to_clean(self, window):

        self.files_to_clean = filedialog.askopenfilenames(title="Select files to clean",
                                                          filetypes=[("All Files", "*.*")])
        if self.files_to_clean:
            files_to_clean_frame = ctk.CTkScrollableFrame(window)
            files_to_clean_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
            files_to_clean_frame.grid_columnconfigure(0, weight=1)

            for i, file in enumerate(self.files_to_clean):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(files_to_clean_frame,
                                                    text=file_name,
                                                    wraplength=400)
                selected_files_label.grid(row=i, column=0, padx=10, pady=3, sticky='nsew')       
            self.check_run()         
    
    def select_save_path(self, window):
        self.save_path = filedialog.askdirectory(title="Save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(window,
                                           text=f"{self.save_path}",
                                           fg_color="transparent",
                                           wraplength=400)
            save_path_label.grid(row=6, column=0, padx=5, pady=5)
            self.check_run()

    def check_run(self):
        if self.auth_code and self.files_to_clean and self.save_path:

            switch_frame = ctk.CTkFrame(self, fg_color="transparent")
            switch_frame.grid(row=7, column=0, padx=5, sticky="nsew")
            switch_frame.grid_rowconfigure(0, weight=1)
            switch_frame.grid_columnconfigure((0,1,2,3), weight=1)
            selected_mode = ctk.StringVar(value="call_marketing")

            mode_label = ctk.CTkLabel(switch_frame,
                                      text="Select run mode: ")
            mode_label.grid(row=0, column=0, padx=5, sticky="nsew")

            # Left radio button
            radio_off = ctk.CTkRadioButton(switch_frame, text="Call Marketing", variable=selected_mode, value="call_marketing")
            radio_off.grid(row=0, column=1, padx=5, sticky="nsew")

            # Right radio button
            radio_on = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Raw Cleaning", variable=selected_mode, value="text_marketing")
            radio_on.grid(row=0, column=2, padx=5, sticky="nsew")

            re_cleaning_button = ctk.CTkRadioButton(switch_frame, text="Text Marketing - Re-Cleaning", variable=selected_mode, value="recleaning")
            re_cleaning_button.grid(row=0, column=3, padx=5, sticky="nsew")

            run_tool_button = ctk.CTkButton(self,
                                            text='RUN TOOL',
                                            height=36,
                                            width=240,
                                            fg_color='#d99125',
                                            hover_color='#ae741e',
                                            text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_autodialer,
                                                                                        self.auth_code,
                                                                                        self.files_to_clean,
                                                                                        self.save_path,
                                                                                        selected_mode.get()))
            run_tool_button.grid(row=8, column=0, padx=10, pady=5)

    def update_list_cleaner(self):
        if self.auth_code:
            self.controller.trigger_tool(update_list_cleaner_file, self.auth_code, self)


class MissingDealsText(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.controller.input_file_check = False
        self.controller.save_path_check = False
        self.files_to_process = False
        self.save_path = False
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((5), weight=1)

        label = ctk.CTkLabel(self,
                             text="Missing Deals Text Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        
        select_file_button = ctk.CTkButton(self,
                                           text='Select files to process',
                                           command=lambda: self.select_files_to_clean(self),
                                           fg_color='#5b5c5c',
                                           hover_color='#424343')
        select_file_button.grid(row=1, column=0, padx=10, pady=5)

        define_save_path_button = ctk.CTkButton(self,
                                                text='Save output files to',
                                                command=lambda: self.select_save_path(self),
                                                fg_color='#5b5c5c',
                                                hover_color='#424343')
        define_save_path_button.grid(row=3, column=0, padx=10, pady=5)

    def select_files_to_clean(self, window):

        self.files_to_process = filedialog.askopenfilenames(title="Select files to clean",
                                                          filetypes=[("All Files", "*.*")])
        if self.files_to_process:
            files_to_clean_frame = ctk.CTkScrollableFrame(window,
                                                          height=80)
            files_to_clean_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
            files_to_clean_frame.grid_columnconfigure(0, weight=1)

            for i, file in enumerate(self.files_to_process):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(files_to_clean_frame,
                                                    text=file_name,
                                                    wraplength=400)
                selected_files_label.grid(row=i, column=0, padx=10, pady=3, sticky='nsew')       
            self.check_run()         
    
    def select_save_path(self, window):
        self.save_path = filedialog.askdirectory(title="Save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(window,
                                           text=f"{self.save_path}",
                                           fg_color="transparent",
                                           wraplength=400)
            save_path_label.grid(row=4, column=0, padx=5, pady=5)
            self.check_run()

    
    def check_run(self):
        if self.files_to_process and self.save_path:
            run_buttons_frame = ctk.CTkFrame(self,
                                             fg_color='transparent')
            run_buttons_frame.grid(row=5, column=0, padx=10, pady=5)
            run_buttons_frame.grid_rowconfigure(0, weight=1)
            run_buttons_frame.grid_columnconfigure((0,1), weight=1)

            run_tool_button = ctk.CTkButton(run_buttons_frame,
                                            text='RUN TOOL',
                                            height=36,
                                            width=240,
                                            fg_color='#d99125',
                                            hover_color='#ae741e',
                                            text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_missing_deals,
                                                                                        self.files_to_process,
                                                                                        self.save_path))
            run_tool_button.grid(row=0, column=0, padx=10, pady=5)

            run_tool_button = ctk.CTkButton(run_buttons_frame,
                                            text='RUN LOOK UP',
                                            height=36,
                                            width=240,
                                            # fg_color='#d99125',
                                            # hover_color='#ae741e',
                                            # text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_missing_deals_lookup,
                                                                                        self.files_to_process,
                                                                                        self.save_path))
            run_tool_button.grid(row=0, column=1, padx=10, pady=5)

class MarketingCleanupTool(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.controller.input_file_check = False
        self.controller.save_path_check = False
        self.pipedrive_file = False
        self.files_to_clean = False
        self.save_path = False
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)

        label = ctk.CTkLabel(self,
                             text="Marketing Cleanup Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        list_cleaner_button = ctk.CTkButton(self,
                                            text="Select pipedrive file",
                                            fg_color='#5b5c5c',
                                            hover_color='#424343',
                                            command=lambda:self.select_cleaner_file(self))
        list_cleaner_button.grid(row=1, column=0, padx=5, pady=5, sticky="ns")

        list_button = ctk.CTkButton(self,
                                    text="Select files to clean",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_files_to_clean(self))
        list_button.grid(row=3, column=0, padx=5, pady=5, sticky="ns")

        list_button = ctk.CTkButton(self,
                                    text="Save output files to",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_save_path(self))
        list_button.grid(row=5, column=0, padx=5, pady=5, sticky="ns")
    
    def select_cleaner_file(self, window):

        self.pipedrive_file = filedialog.askopenfilename(title="Select list cleaner file",
                                                        filetypes=[("All Files", "*.*")])
        if self.pipedrive_file:
            cleaner_file_label = ctk.CTkLabel(window,
                                              text=f"{os.path.basename(self.pipedrive_file)}",
                                              fg_color="transparent")
            cleaner_file_label.grid(row=2, column=0, padx=5, pady=5)
            self.check_run()

    def select_files_to_clean(self, window):

        self.files_to_clean = filedialog.askopenfilenames(title="Select files to clean",
                                                          filetypes=[("All Files", "*.*")])
        if self.files_to_clean:
            files_to_clean_frame = ctk.CTkScrollableFrame(window,
                                                          height=80)
            files_to_clean_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
            files_to_clean_frame.grid_columnconfigure(0, weight=1)

            for i, file in enumerate(self.files_to_clean):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(files_to_clean_frame,
                                                    text=file_name,
                                                    wraplength=400)
                selected_files_label.grid(row=i, column=0, padx=10, pady=3, sticky='nsew')       
            self.check_run()         
    
    def select_save_path(self, window):
        self.save_path = filedialog.askdirectory(title="Save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(window,
                                           text=f"{self.save_path}",
                                           fg_color="transparent",
                                           wraplength=400)
            save_path_label.grid(row=6, column=0, padx=5, pady=5)
            self.check_run()

    def check_run(self):
        if self.pipedrive_file and self.files_to_clean and self.save_path:
            run_tool_button = ctk.CTkButton(self,
                                            text='RUN TOOL',
                                            height=36,
                                            width=240,
                                            fg_color='#d99125',
                                            hover_color='#ae741e',
                                            text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_marketing_cleanup,
                                                                                        self.files_to_clean,
                                                                                        self.pipedrive_file,
                                                                                        self.save_path))
            run_tool_button.grid(row=7, column=0, padx=10, pady=5)

class WellMatchingTool(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.controller.input_file_check = False
        self.controller.save_path_check = False
        self.db_file = False
        self.files_to_clean = False
        self.save_path = False
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)

        label = ctk.CTkLabel(self,
                             text="Well Matching Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        select_db_file_button = ctk.CTkButton(self,
                                            text="Select DB Browser file",
                                            fg_color='#5b5c5c',
                                            hover_color='#424343',
                                            command=lambda:self.select_db_file(self))
        select_db_file_button.grid(row=1, column=0, padx=5, pady=5, sticky="ns")

        list_button = ctk.CTkButton(self,
                                    text="Select files to process",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_files_to_clean(self))
        list_button.grid(row=3, column=0, padx=5, pady=5, sticky="ns")

        list_button = ctk.CTkButton(self,
                                    text="Save output files to",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_save_path(self))
        list_button.grid(row=5, column=0, padx=5, pady=5, sticky="ns")
    
    def select_db_file(self, window):

        self.db_file = filedialog.askopenfilename(title="Select list cleaner file",
                                                        filetypes=[("Database file", "*.db")])
        if self.db_file:
            cleaner_file_label = ctk.CTkLabel(window,
                                              text=f"{os.path.basename(self.db_file)}",
                                              fg_color="transparent")
            cleaner_file_label.grid(row=2, column=0, padx=5, pady=5)
            self.check_run()

    def select_files_to_clean(self, window):

        self.files_to_clean = filedialog.askopenfilenames(title="Select files to clean",
                                                          filetypes=[("All Files", "*.*")])
        if self.files_to_clean:
            files_to_clean_frame = ctk.CTkScrollableFrame(window,
                                                          height=80)
            files_to_clean_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
            files_to_clean_frame.grid_columnconfigure(0, weight=1)

            for i, file in enumerate(self.files_to_clean):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(files_to_clean_frame,
                                                    text=file_name,
                                                    wraplength=400)
                selected_files_label.grid(row=i, column=0, padx=10, pady=3, sticky='nsew')       
            self.check_run()         
    
    def select_save_path(self, window):
        self.save_path = filedialog.askdirectory(title="Save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(window,
                                           text=f"{self.save_path}",
                                           fg_color="transparent",
                                           wraplength=400)
            save_path_label.grid(row=6, column=0, padx=5, pady=5)
            self.check_run()

    def check_run(self):
        if self.db_file and self.files_to_clean and self.save_path:
            run_tool_button = ctk.CTkButton(self,
                                            text='RUN TOOL',
                                            height=36,
                                            width=240,
                                            fg_color='#d99125',
                                            hover_color='#ae741e',
                                            text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_well_matching_tool,
                                                                                        self.db_file,
                                                                                        self.files_to_clean,
                                                                                        self.save_path))
            run_tool_button.grid(row=7, column=0, padx=10, pady=5)

class C3AutomationTool(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.controller.input_file_check = False
        self.controller.save_path_check = False
        self.db_file = False
        self.files_to_clean = False
        self.save_path = False
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)

        label = ctk.CTkLabel(self,
                             text="C3 Automation Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        select_db_file_button = ctk.CTkButton(self,
                                            text="Select pipedrive file",
                                            fg_color='#5b5c5c',
                                            hover_color='#424343',
                                            command=lambda:self.select_db_file(self))
        select_db_file_button.grid(row=1, column=0, padx=5, pady=5, sticky="ns")

        list_button = ctk.CTkButton(self,
                                    text="Select files to process",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_files_to_clean(self))
        list_button.grid(row=3, column=0, padx=5, pady=5, sticky="ns")

        list_button = ctk.CTkButton(self,
                                    text="Save output files to",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_save_path(self))
        list_button.grid(row=5, column=0, padx=5, pady=5, sticky="ns")
    
    def select_db_file(self, window):

        self.db_file = filedialog.askopenfilename(title="Select pipedrive file",
                                                        filetypes=[("Pipedrive file", "*.*")])
        if self.db_file:
            cleaner_file_label = ctk.CTkLabel(window,
                                              text=f"{os.path.basename(self.db_file)}",
                                              fg_color="transparent")
            cleaner_file_label.grid(row=2, column=0, padx=5, pady=5)
            self.check_run()

    def select_files_to_clean(self, window):

        self.files_to_clean = filedialog.askopenfilenames(title="Select files to process",
                                                          filetypes=[("All Files", "*.*")])
        if self.files_to_clean:
            files_to_clean_frame = ctk.CTkScrollableFrame(window,
                                                          height=80)
            files_to_clean_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
            files_to_clean_frame.grid_columnconfigure(0, weight=1)

            for i, file in enumerate(self.files_to_clean):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(files_to_clean_frame,
                                                    text=file_name,
                                                    wraplength=400)
                selected_files_label.grid(row=i, column=0, padx=10, pady=3, sticky='nsew')       
            self.check_run()         
    
    def select_save_path(self, window):
        self.save_path = filedialog.askdirectory(title="Save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(window,
                                           text=f"{self.save_path}",
                                           fg_color="transparent",
                                           wraplength=400)
            save_path_label.grid(row=6, column=0, padx=5, pady=5)
            self.check_run()

    def check_run(self):
        if self.db_file and self.files_to_clean and self.save_path:
            run_tool_button = ctk.CTkButton(self,
                                            text='RUN TOOL',
                                            height=36,
                                            width=240,
                                            fg_color='#d99125',
                                            hover_color='#ae741e',
                                            text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_c3_tool,
                                                                                        self.db_file,
                                                                                        self.files_to_clean,
                                                                                        self.save_path))
            run_tool_button.grid(row=7, column=0, padx=10, pady=5)

class NameParsingTool(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.controller.input_file_check = False
        self.controller.save_path_check = False
        self.db_file = False
        self.files_to_clean = False
        self.save_path = False
        self.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        label = ctk.CTkLabel(self,
                             text="Name Parsing Tool",
                             font=ctk.CTkFont(
                                 size=30,
                                 weight='bold'
                             ))
        label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        list_button = ctk.CTkButton(self,
                                    text="Select files to process",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_files_to_clean(self))
        list_button.grid(row=1, column=0, padx=5, pady=5, sticky="ns")

        list_button = ctk.CTkButton(self,
                                    text="Save output files to",
                                    fg_color='#5b5c5c',
                                    hover_color='#424343',
                                    command=lambda:self.select_save_path(self))
        list_button.grid(row=3, column=0, padx=5, pady=5, sticky="ns")
    
    def select_files_to_clean(self, window):

        self.files_to_clean = filedialog.askopenfilenames(title="Select files to process",
                                                          filetypes=[("All Files", "*.*")])
        if self.files_to_clean:
            files_to_clean_frame = ctk.CTkScrollableFrame(window,
                                                          height=80)
            files_to_clean_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
            files_to_clean_frame.grid_columnconfigure(0, weight=1)

            for i, file in enumerate(self.files_to_clean):
                file_name = os.path.basename(file)
                selected_files_label = ctk.CTkLabel(files_to_clean_frame,
                                                    text=file_name,
                                                    wraplength=400)
                selected_files_label.grid(row=i, column=0, padx=10, pady=3, sticky='nsew')       
            self.check_run()         
    
    def select_save_path(self, window):
        self.save_path = filedialog.askdirectory(title="Save directory")
        if self.save_path:
            save_path_label = ctk.CTkLabel(window,
                                           text=f"{self.save_path}",
                                           fg_color="transparent",
                                           wraplength=400)
            save_path_label.grid(row=4, column=0, padx=5, pady=5)
            self.check_run()

    def check_run(self):
        if self.files_to_clean and self.save_path:
            run_tool_button = ctk.CTkButton(self,
                                            text='RUN TOOL',
                                            height=36,
                                            width=240,
                                            fg_color='#d99125',
                                            hover_color='#ae741e',
                                            text_color='#141414',
                                            corner_radius=50,
                                            font=ctk.CTkFont(size=18, weight='bold'),
                                            command=lambda:self.controller.trigger_tool(run_name_parsing,
                                                                                        self.files_to_clean,
                                                                                        self.save_path))
            run_tool_button.grid(row=5, column=0, padx=10, pady=5)

def main() -> None:

    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
