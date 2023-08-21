import src.scripts.get_stock_image as stock_img
import src.stock_manager as sm
import os

def main():
    script_name = input('Enter script name: ')
    if script_name == "stock_image":
        stock_img.main()

    if script_name == "update_stock":
        sm.main()

if __name__ == '__main__':
    main()