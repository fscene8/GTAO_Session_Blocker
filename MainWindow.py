from SnifferThread import SnifferThread
from tksheet import Sheet
from tkinter import messagebox
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter import Menu
import tkinter.simpledialog
import PopUps
from datetime import datetime
import psutil, os, re, pickle, firewall, time
import tkinter as tk

class MainWindow(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.runSnifferThread()
        self.firewallEnabled = False
        self.snifferThreadRunning = True
        self.localIP = ''
        self.ipWhiteListDictionary = {}

        self.title('GTAO Session Blocker')
        
        self.setMenuElements()
        self.setTopElements()
        self.setIPScannerTable()
        
        self.spawnMiddleScreen()

        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight = 1)

        self.loadWhiteList()
        self.printDictionary()

        self.resizable(False, False) 
    
    def cleanup(self):
        firewall.delete_firewall_rule()
        self.snifferThread.stop()

    def runSnifferThread(self):
        self.snifferThread = SnifferThread()

        # Kills the thread if parent dies
        self.snifferThread.daemon = True
        self.snifferThread.start()
        
    def spawnMiddleScreen(self):
        # Gets the requested values of the height and width.
        windowWidth = self.winfo_reqwidth()
        windowHeight = self.winfo_reqheight()
        
        # Gets both half the screen width/height and window width/height
        positionRight = int(self.winfo_screenwidth()/2 - windowWidth/2)
        positionDown = int(self.winfo_screenheight()/2 - windowHeight)
        
        # Positions the window in the center of the page.
        self.geometry("+{}+{}".format(positionRight, positionDown))         

    def setMenuElements(self):
        menubar = Menu(self)
        self.config(menu=menubar)

        # create a menu
        file_menu = Menu(menubar,tearoff=False)
        # add a menu item to the menu
        file_menu.add_command(label='Exit',command=self.destroy)
        # add the File menu to the menubar
        menubar.add_cascade(label="File",menu=file_menu)

        # create the Help menu
        help_menu = Menu(menubar,tearoff=0)
        help_menu.add_command(label='How To', command=PopUps.HowTo )
        help_menu.add_command(label='About', command=PopUps.About )
        # add the Help menu to the menubar
        menubar.add_cascade(label="Help",menu=help_menu)

    def getGTAVPath(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.name() == "GTA5.exe":
                    return proc.cwd()+'\\'+ 'GTA5.exe'
            except psutil.AccessDenied:
                continue
        return ''

    def setTopElements(self):
        self.topframe = tk.Frame(self)

        # Row 0
        tk.Label(self.topframe, text="GTA V exe path").grid(row=0,column=0, padx=5, pady=2, sticky="w")
        self.entryGTAPath = tk.Entry(self.topframe, width=30)
        self.entryGTAPath.grid(row=0, column=1, padx=5, pady=2, columnspan=3,  sticky="nwe")
        self.entryGTAPath.insert(0,self.getGTAVPath())
        self.openfiledialog = ttk.Button(self.topframe,text='Get GTA V Path',command=self.openGTA5Path,width=18)
        self.openfiledialog.grid(row=0, column=4, padx=5, pady=2,  sticky="nwe")

        # Row 1
        tk.Label(self.topframe, text="Add IP Manually").grid(row=1,column=0, padx=5, pady=2, sticky="w")
        self.entryAddIP = tk.Entry(self.topframe,width=30)
        self.entryAddIP.grid(row=1, column=1, padx=5, pady=2, columnspan=3,  sticky="nwe")
        self.btnAddIP = tk.Button(self.topframe, text="Add IP to whitelist",command=self.addIPManually,width=15)
        self.btnAddIP.grid(row=1,column=4, padx=5, pady=2, sticky="nwe")

        # Row 2        
        tk.Label(self.topframe, text="Whitelist ->").grid(row=2,column=0, padx=5, pady=2,rowspan=1, sticky="w")
        tk.Label(self.topframe, text="Right-Click to delete").grid(row=3,column=0, padx=5, rowspan=1, sticky="sw")
        tk.Label(self.topframe, text="or insert/edit note").grid(row=4,column=0, padx=5, rowspan=1, sticky="nw")

        # Set whitelist table
        self.setWhiteListTable()

        # Row 8
        tk.Label(self.topframe, text="Step 1 >").grid(row=8,column=0, padx=5, pady=2, sticky="w")
        tk.Label(self.topframe, text="Suspend GTA to be the alone and be host session").grid(row=8,column=1, padx=5, pady=2,columnspan=2, sticky="w")
        self.btnSuspendProc = tk.Button(self.topframe, text="Suspend for 10 sec",command=self.suspendGTA)
        self.btnSuspendProc.grid(row=8,column=4, padx=5, pady=2, columnspan=1, sticky="we")

        # Row 9     
        tk.Label(self.topframe, text="Step 2 >").grid(row=9,column=0, padx=5, pady=2, sticky="w")
        tk.Label(self.topframe, text="Invite your friends to join your session and whitelist their IP").grid(row=9,column=1, padx=5, pady=2,columnspan=4, sticky="w")
        
        # Row 10     
        tk.Label(self.topframe, text="Step 3 >").grid(row=10,column=0, padx=5, pady=2, sticky="w")
        tk.Label(self.topframe, text="Toggle on the firewall after they have joined").grid(row=10,column=1, padx=5, pady=2,columnspan=2, sticky="w")
        self.EnableFirewall = tk.Button(self.topframe, text="Firewall OFF", command=self.togglefirewall,background="yellow",foreground="black")
        self.EnableFirewall.grid(row=10,column=4, padx=5, pady=2, columnspan=1, sticky="we")
        
        # Row 12    
        tk.Label(self.topframe, text="IP in session. Right click an IP address and Add to White List").grid(row=12,column=0, padx=5, pady=2,columnspan=2, sticky="w")
        self.btnToggleScanIP = tk.Button(self.topframe, text="Scan ON", command=self.toggleScanIP, background="green",foreground="white")
        self.btnToggleScanIP.grid(row=12,column=2, padx=5, pady=1, columnspan=2, sticky="we")
        self.btnRefreshIPData = tk.Button(self.topframe, text="Clear table below", command=self.clearIPTable)
        self.btnRefreshIPData.grid(row=12,column=4, padx=5, pady=2, sticky="we")
        #self.topframe.pack(padx=10,pady=10)
        self.topframe.grid(row = 0, column = 0, sticky = "n")

    def setWhiteListTable(self):
        headers = ['IP Address','Notes']
        self.ipwhitelistsheet = Sheet(self.topframe,
                            page_up_down_select_row = True,
                            expand_sheet_if_paste_too_big = True,
                            headers = [f"{c}" for c in headers],
                            height = 180
                            )
        
        self.ipwhitelistsheet.column_width(column = 0, width = 120) 
        self.ipwhitelistsheet.column_width(column = 1, width = 250)                            
        self.ipwhitelistsheet.enable_bindings(("single_select", #"single_select" or "toggle_select"
                                    "drag_select",   #enables shift click selection as well
                                    "select_all",
                                    "column_drag_and_drop",
                                    "row_drag_and_drop",
                                    "column_select",
                                    "row_select",
                                    "column_width_resize",
                                    "double_click_column_resize",
                                    "row_width_resize",
                                    "column_height_resize",
                                    "arrowkeys",
                                    "row_height_resize",
                                    "double_click_row_resize",
                                    "right_click_popup_menu",
                                    "rc_select",
                                    "copy"
                                    ))
        self.ipwhitelistsheet.grid(row=2,column=1, padx=5, pady=2, columnspan=5, rowspan=4,  sticky="nwe")
        self.ipwhitelistsheet.popup_menu_add_command("Insert/Edit Note", self.whitelistInsertNotes) 
        self.ipwhitelistsheet.popup_menu_add_command("Delete Entry", self.whitelistDeleteEntry)  

    def setIPScannerTable(self):
        headers = ['IP Address','Country', 'Firstseen', 'Lastseen', 'Ago', 'Packets In', 'Region', 'City']
        self.ipscannerframe = tk.Frame(self)
        self.ipscannerframe.grid_columnconfigure(0, weight = 1)
        self.ipscannerframe.grid_rowconfigure(0, weight = 1)
        self.ipscannersheet = Sheet(self.ipscannerframe,
                            page_up_down_select_row = True,
                            expand_sheet_if_paste_too_big = True,
                            headers = [f"{c}" for c in headers],
                            height = 300 #height and width arguments are optional
                            )
        
        self.ipscannersheet.column_width(column = 0, width = 120) 
        self.ipscannersheet.column_width(column = 1, width = 50)  
        self.ipscannersheet.column_width(column = 2, width = 60) 
        self.ipscannersheet.column_width(column = 3, width = 60)  
        self.ipscannersheet.column_width(column = 4, width = 60)  
        self.ipscannersheet.column_width(column = 5, width = 60)   
        self.ipscannersheet.column_width(column = 6, width = 150)   
        self.ipscannersheet.column_width(column = 7, width = 350)                           
        self.ipscannersheet.enable_bindings(("single_select", #"single_select" or "toggle_select"
                                    "drag_select",   #enables shift click selection as well
                                    "select_all",
                                    "column_drag_and_drop",
                                    "row_drag_and_drop",
                                    "column_select",
                                    "row_select",
                                    "column_width_resize",
                                    "double_click_column_resize",
                                    "row_width_resize",
                                    "column_height_resize",
                                    "arrowkeys",
                                    "row_height_resize",
                                    "double_click_row_resize",
                                    "right_click_popup_menu",
                                    "rc_select",
                                    "copy"
                                    ))
        self.ipscannerframe.grid(row = 1, column = 0, sticky = "swe")
        self.ipscannersheet.grid(row = 1, column = 0, sticky = "swe")
        self.ipscannersheet.popup_menu_add_command("Add To Whitelist", self.rcAddToWhitelist) 
        self.ipscannersheet.popup_menu_add_command("Delete Row Entry", self.rcDeleteRow) 
    
    def openGTA5Path(self):
        gtapath = self.getGTAVPath()
        if gtapath == '':
            # file type
            filetypes = ('exe files', '*.exe')
            # show the open file dialog
            f = fd.askopenfilename(title="GTA V Exe Path", filetypes =(("GTA5", "GTA5.exe"),("EXE","*.exe")))
            self.entryGTAPath.insert(0,f.replace('/','\\'))
        else:
            self.entryGTAPath.insert(0,gtapath)
   
    def addIPManually(self):
        if not len(self.entryAddIP.get().strip()) or not self.isValidIP(self.entryAddIP.get().strip()) :
            messagebox.showinfo('Invalid IP', 'Please key in a valid IP address')  
        else:
            iptoadd = self.entryAddIP.get().strip()
            if self.ipwhitelistsheet.total_rows() > 0:
                for i in range(self.ipwhitelistsheet.total_rows()):
                    if iptoadd in self.ipwhitelistsheet.get_cell_data(i,0).strip():
                        messagebox.showinfo('Information',"IP is already in the white list.")
                        return False
            self.ipwhitelistsheet.insert_row([iptoadd,''])
            self.ipwhitelistsheet.display_columns( refresh = True)
            self.ipWhiteListDictionary[self.entryAddIP.get().strip()] = ''
            self.saveWhiteList()

    def isValidIP(self,address):
        pat = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        check = pat.match(address)
        if check:
            return True
        else:
            return False

    def rcAddToWhitelist(self, event = None):
        if self.ipscannersheet.get_currently_selected()[0] == 'row':
            iptoadd = self.ipscannersheet.get_cell_data(self.ipscannersheet.get_currently_selected()[1], 0)
        elif self.ipscannersheet.get_currently_selected()[0] == 'column':
            messagebox.showinfo('Column Selected', 'Please select a row. Not a column!')
            return False
        else: 
            iptoadd = self.ipscannersheet.get_cell_data(self.ipscannersheet.get_currently_selected()[0], 0)

        if self.ipwhitelistsheet.total_rows() > 0:
            for i in range(self.ipwhitelistsheet.total_rows()):
                if iptoadd in self.ipwhitelistsheet.get_cell_data(i,0):
                    messagebox.showinfo('Information',"IP is already in the white list.")
                    return False
        self.ipwhitelistsheet.insert_row([iptoadd,''])
        self.ipwhitelistsheet.display_columns(refresh = True)
        self.ipWhiteListDictionary[iptoadd] = ''
        self.saveWhiteList()
        return True

    def rcDeleteRow(self):
        if self.ipscannersheet.get_currently_selected()[0] == 'row':
            x = self.ipscannersheet.get_currently_selected()[1]
            iptopop = self.ipscannersheet.get_cell_data(self.ipscannersheet.get_currently_selected()[1], 0)
        elif self.ipscannersheet.get_currently_selected()[0] == 'column':
            messagebox.showinfo('Column Selected', 'Please select a row. Not a column!')
            return False
        else: 
            x = self.ipscannersheet.get_currently_selected()[0]
            iptopop = self.ipscannersheet.get_cell_data(self.ipscannersheet.get_currently_selected()[0], 0)
        
        self.snifferThread.ipDictionary.pop(iptopop) 
        self.ipscannersheet.delete_row(x)    
        self.ipscannersheet.display_columns(refresh = True)

    def whitelistInsertNotes(self):
        if self.ipwhitelistsheet.get_currently_selected()[0] == 'row':
            x = self.ipwhitelistsheet.get_currently_selected()[1]
        elif self.ipwhitelistsheet.get_currently_selected()[0] == 'column':
            messagebox.showinfo('Column Selected', 'Please select a row. Not a column!')
            return False
        else: 
            x = self.ipwhitelistsheet.get_currently_selected()[0]

        # the input dialog
        USER_INP = tkinter.simpledialog.askstring(title="Insert Note",prompt="Please key in your note below:")
        self.ipwhitelistsheet.set_cell_data(x, 1,USER_INP)
        self.ipwhitelistsheet.display_columns(refresh = True)
        self.ipWhiteListDictionary[self.ipwhitelistsheet.get_cell_data(x, 0)] = USER_INP
        self.saveWhiteList()

    def whitelistDeleteEntry(self):
        if self.ipwhitelistsheet.get_currently_selected()[0] == 'row':
            x = self.ipwhitelistsheet.get_currently_selected()[1]
        elif self.ipwhitelistsheet.get_currently_selected()[0] == 'column':
            messagebox.showinfo('Column Selected', 'Please select a row. Not a column!')
            return False
        else: 
            x = self.ipwhitelistsheet.get_currently_selected()[0]

        self.ipWhiteListDictionary.pop(self.ipwhitelistsheet.get_cell_data(x, 0))
        self.ipwhitelistsheet.delete_row(x)    
        self.ipwhitelistsheet.display_columns(refresh = True)
        self.saveWhiteList()
       
    def suspendGTA(self):
        psid = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.name() == "GTA5.exe":
                    psid = proc.pid
            except psutil.AccessDenied:
                continue
        if psid:
            gta_process = psutil.Process(psid)
           
            gta_process.suspend()
            seconds = 10
            while seconds != 0:
                time.sleep(1)
                seconds -= 1
            gta_process.resume()
        else:
            messagebox.showinfo('Error', 'Unable to find GTA processs')  

    def togglefirewall(self):
        if self.firewallEnabled:
            firewall.delete_firewall_rule()
            self.EnableFirewall.configure(text="Firewall OFF",background="yellow",foreground="black")
        else:
            programpath = self.entryGTAPath.get().strip()
            if os.path.isfile(programpath):
                self.enableFirewall(programpath)
                time.sleep(0.5)
                self.EnableFirewall.configure(text="Firewall ON",background="green",foreground="white")
                
                self.snifferThreadRunning = True
                self.toggleScanIP()
            else:
                messagebox.showinfo('Missing Game Path','Missing/invalid GTA Online EXE path!')
        self.firewallEnabled = not self.firewallEnabled 

    def enableFirewall(self, programpath):
        success = firewall.add_firewall_rule(programpath)
        if success:
        # Add scope
            for ip in list(self.ipWhiteListDictionary.keys()):
                firewall.add_white_list(str(ip).strip()) 
        # Enable Firewall
        time.sleep(2)
        firewall.enable_firewall_rule()

    def toggleScanIP(self):
        if self.snifferThreadRunning:
            self.snifferThread.pause()
            self.btnToggleScanIP.configure(text="Scan OFF",background="yellow",foreground="black")
        else: 
            self.snifferThread.resume()
            self.btnToggleScanIP.configure(text="Scan ON",background="green",foreground="white")
        self.snifferThreadRunning = not self.snifferThreadRunning

    def clearIPTable(self):
        self.snifferThread.clearIPDictionary()
        self.ipscannersheet.display_columns(refresh = True )

    def printDictionary(self) -> None:
        if self.ipscannersheet.total_rows() > 0:
            for i in range(self.ipscannersheet.total_rows()):
                self.ipscannersheet.delete_row(self.ipscannersheet.total_rows()-1)  
        for ip, gtaIPData in self.snifferThread.getIPDictionary().items():
            self.ipscannersheet.insert_row([ip, gtaIPData.country, gtaIPData.firstseen.strftime("%H:%M:%S"), gtaIPData.lastseen.strftime("%H:%M:%S"), str(datetime.now() - gtaIPData.lastseen).split(".")[0], gtaIPData.packetsin,gtaIPData.region, gtaIPData.city])
        self.ipscannersheet.display_columns(refresh = True)
        self.after(1000, self.printDictionary)

    def saveWhiteList(self):
        with open('ipwhitelist.p', 'wb') as fp:
            pickle.dump(self.ipWhiteListDictionary, fp, protocol=pickle.HIGHEST_PROTOCOL)

    def loadWhiteList(self):
        if os.path.isfile('ipwhitelist.p'):
            with open('ipwhitelist.p', 'rb') as fp:
                self.ipWhiteListDictionary = pickle.load(fp)
            for k,v in self.ipWhiteListDictionary.items():
                self.ipwhitelistsheet.insert_row([k,v])
        self.ipwhitelistsheet.display_columns(refresh = True)
        