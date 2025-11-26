from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QMenu

class ActionHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        self.create_actions()

    def create_actions(self):
        # Launch actions
        self.launch_action = QAction("Launch Game", self.main_window)
        self.launch_action.setShortcut(QKeySequence("Ctrl+L"))
        self.launch_action.triggered.connect(self.main_window.launch_page.launch_button.click)

        # Navigation actions
        self.nav_launch_action = QAction("Go to Launch Page", self.main_window)
        self.nav_launch_action.setShortcut(QKeySequence("Ctrl+1"))
        self.nav_launch_action.triggered.connect(self.main_window.nav_launch_button.click)

        self.nav_mods_action = QAction("Go to Mods Page", self.main_window)
        self.nav_mods_action.setShortcut(QKeySequence("Ctrl+2"))
        self.nav_mods_action.triggered.connect(self.main_window.nav_mods_button.click)

        self.nav_settings_action = QAction("Go to Settings Page", self.main_window)
        self.nav_settings_action.setShortcut(QKeySequence("Ctrl+4"))
        self.nav_settings_action.triggered.connect(lambda: self.main_window.switch_page(3, self.main_window.nav_settings_button))
        
        self.nav_browse_mods_action = QAction("Browse Mods", self.main_window)
        self.nav_browse_mods_action.setShortcut(QKeySequence("Ctrl+3"))
        self.nav_browse_mods_action.triggered.connect(lambda: self.main_window.switch_page(2, self.main_window.nav_browse_mods_button))
        
        # Mod manager actions
        self.refresh_mods_action = QAction("Refresh Mods List", self.main_window)
        self.refresh_mods_action.setShortcut(QKeySequence("F5"))
        self.refresh_mods_action.triggered.connect(self.main_window.mods_page.populate_mods_list)

        # Other actions
        self.quit_action = QAction("Quit", self.main_window)
        self.quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_action.triggered.connect(self.main_window.close)

    def create_main_context_menu(self):
        menu = QMenu(self.main_window)
        menu.addAction(self.launch_action)
        menu.addSeparator()
        menu.addAction(self.nav_launch_action)
        menu.addAction(self.nav_mods_action)
        menu.addAction(self.nav_browse_mods_action)
        menu.addAction(self.nav_settings_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)
        return menu
        
    def create_mods_context_menu(self):
        menu = QMenu(self.main_window)
        menu.addAction(self.refresh_mods_action)
        menu.addAction(QAction("Open Mods Folder", self.main_window, triggered=self.main_window.mods_page.open_mods_folder))
        menu.addSeparator()
        
        selected_items = self.main_window.mods_page.mod_list_widget.selectedItems()
        if selected_items:
            delete_action = QAction("Delete Selected Mod", self.main_window, triggered=self.main_window.mods_page.delete_selected_mod)
            delete_action.setShortcut(QKeySequence("Delete"))
            menu.addAction(delete_action)

        return menu

    def create_menu_bar(self):
        menu_bar = self.main_window.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.launch_action)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        # Navigate Menu
        navigate_menu = menu_bar.addMenu("&Navigate")
        navigate_menu.addAction(self.nav_launch_action)
        navigate_menu.addAction(self.nav_mods_action)
        navigate_menu.addAction(self.nav_browse_mods_action)
        navigate_menu.addAction(self.nav_settings_action)
        
        # Mods Menu
        mods_menu = menu_bar.addMenu("&Mods")
        mods_menu.addAction(self.refresh_mods_action)
        mods_menu.addAction(QAction("Open Mods Folder", self.main_window, triggered=self.main_window.mods_page.open_mods_folder))

def setup_actions_and_menus(main_window):
    handler = ActionHandler(main_window)
    main_window.action_handler = handler
    
    # Add shortcuts that should be active globally
    main_window.addActions([
        handler.launch_action,
        handler.nav_launch_action,
        handler.nav_mods_action,
        handler.nav_browse_mods_action,
        handler.nav_settings_action,
        handler.quit_action,
        handler.refresh_mods_action
    ])

    # Create menu bar
    handler.create_menu_bar()

    # Main window context menu
    def show_main_context_menu(pos):
        menu = handler.create_main_context_menu()
        menu.exec(main_window.mapToGlobal(pos))

    main_window.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    main_window.customContextMenuRequested.connect(show_main_context_menu)
    
    # Mods page context menu
    def show_mods_context_menu(pos):
        menu = handler.create_mods_context_menu()
        menu.exec(main_window.mods_page.mod_list_widget.mapToGlobal(pos))
        
    main_window.mods_page.mod_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    main_window.mods_page.mod_list_widget.customContextMenuRequested.connect(show_mods_context_menu)
