# nhận giá trị từ bàn phím
# while True:
#     print('Mời bạn nhập giá trị s = ')
#     s = input()
#     if s == 'k':
#         print('bạn đã nhập đúng')
#     elif s == 'q':
#         print('Thoát thoi')
#         break
#     else:
#         print('giá trị bạn nhập vào là: ', s)


from pynput import keyboard


def keyPressed(key):
    print(key)
    if key == keyboard.Key.right:
        print('ok ok right')

    if isinstance(key, keyboard.KeyCode):
        print('bạn vừa bấm', key.char)


def keyReleased(key):
    # Do something ...
    print('say hi')
    if key == keyboard.Key.esc:
        return False


with keyboard.Listener(on_press=keyPressed, on_release=keyReleased) as listener:
    listener.join()

# while True:
#     i = input()
#     print(i)
#     if i == ord('w'):
#         print('hello')