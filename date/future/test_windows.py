import pygetwindow as gw
import pyautogui
from pywinauto import application


def get_control_id(window_title, control_title):
    try:
        # Tìm cửa sổ theo tiêu đề
        window = gw.getWindowsWithTitle(window_title)[0]

        # Kích thước và vị trí của cửa sổ
        left, top, right, bottom = window.left, window.top, window.right, window.bottom

        # Chuyển đổi tọa độ global thành tọa độ cục bộ trong cửa sổ
        local_x, local_y = pyautogui.position()
        local_x -= left
        local_y -= top

        # Lấy control ID của ô dữ liệu tại vị trí local
        control_id = pyautogui.getPixel(local_x, local_y)

        return control_id

    except IndexError:
        print("Không tìm thấy cửa sổ có tiêu đề:", window_title)
        return None


def get_running_windows_titles():
    # Lấy danh sách các cửa sổ đang chạy
    windows = gw.getAllTitles()
    return windows


# def get_input_controls(window_title):
#     # Mở ứng dụng
#     app = application.Application().connect(title="")
#     print(app)
#     # Lấy cửa sổ chính
#     window = app.window(title=window_title)
#
#     # Lấy tất cả các control trong cửa sổ
#     controls = window.descendants()
#
#     # Lọc ra các control là ô input dữ liệu (textbox)
#     input_controls = [control for control in controls if control.wrapper_object().GetClassName() == "Edit"]
#
#     return input_controls
#
# window_title = "Hercules"
#
# window = gw.getWindowsWithTitle("Hercules")[0]
#
# # input_controls = get_input_controls(window_title)
# #
# # # In thông tin về các ô input
# # for control in input_controls:
# #     print("Control ID:", control.wrapper_object().GetHandle())
# #     print("Class Name:", control.wrapper_object().GetClassName())
# #     print("Text:", control.wrapper_object().GetWindowText())
# #     print("---")
#
# # Lấy và in danh sách các tiêu đề của cửa sổ đang chạy
# window_titles = get_running_windows_titles()
# for title in window_titles:
#     # print(title)
#     pass
#
# # Thay thế "Window Title" và "Control Title" bằng thông tin thực của ứng dụng
# window_title = "Hercules"
# control_title = "Control Title"
# # control_id = get_control_id(window_title, control_title)
#
# window = gw.getWindowsWithTitle("Hercules")[0]
# print(window.descendants())

app = application.Application().connect(title="node.txt - Notepad")
window = app.window(title='node.txt - Notepad', top_level_only=True)
# print(window)
# Lấy cửa sổ chính
# window = app.window(title="Qt Designer")

# Lấy tất cả các control trong cửa sổ
controls = window.descendants()

# Lọc ra các control là ô input dữ liệu (textbox)
# input_controls = [control for control in controls if control.wrapper_object().GetClassName() == "Edit"]
# print(controls)
# for control in controls:
#     print(control)
# print(gw.getAllTitles())