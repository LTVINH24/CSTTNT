"""
Chương trình chính để chạy các test thuật toán tìm đường.
"""
import sys
import os
import time
from src.tests.test_pathfinding import run_algorithm_tests
from src.pathfinding import (
    a_star_pathfinder,
    breadth_first_search_path_finder,
    depth_first_search_path_finder,
    ucs_pathfinder
)
def menu():
    """Trình bày menu danh sách các thuật toán cần test."""
    os.system('cls')
    print("\n" + "-"*50)
    print("CHỌN THUẬT TOÁN TÌM ĐƯỜNG")
    print("-"*50)
    print("1. BFS (Breadth-First Search) - Tìm kiếm theo chiều rộng")
    print("2. DFS (Depth-First Search) - Tìm kiếm theo chiều sâu")
    print("3. UCS - Thuật toán tìm đường ngắn nhất")
    print("4. A* - Thuật toán tìm đường đi tốt nhất dựa vào heuristic và chi phí")
    print("0. Thoát chương trình")
    print("-"*50)

def get_input(prompt, valid_range):
    """Người dùng nhập số để chọn thuật toán."""
    while True:
        try:
            value = int(input(prompt))
            if value in valid_range:
                return value
            print(f"Lỗi: Vui lòng nhập giá trị hợp lệ ({min(valid_range)}-{max(valid_range)})")
        except ValueError:
            print("Lỗi: Vui lòng nhập một số nguyên.")

def main():
    """Main function to display menu and run the selected pathfinding algorithm tests."""
    # Map algorithm numbers to algorithm functions and names
    algorithms = {
        1: (breadth_first_search_path_finder, "BFS"),
        2: (depth_first_search_path_finder, "DFS"),
        3: (ucs_pathfinder, "UCS"),
        4: (a_star_pathfinder, "A*")
    }

    while True:
        menu()
        choice = get_input("Nhập lựa chọn của bạn (0-4): ", range(6))

        if choice == 0:
            print("Kết thúc chương trình")
            sys.exit(0)

        # Select algorithm
        pathfinder, algorithm_name = algorithms[choice]

        # Ask for simulation duration
        print(f"\nBạn chọn thuật toán: {algorithm_name}")

        print(f"\nBắt đầu chạy các test case với thuật toán {algorithm_name}...")
        time.sleep(1.5)  # Give user time to read

        # Run tests with selected algorithm
        run_algorithm_tests(
            pathfinder=pathfinder,
            algorithm_name=algorithm_name
        )
        # Ask if user wants to continue
        print("\nTất cả các test case đã hoàn thành.")
        continue_choice = input("Bạn có muốn tiếp tục với thuật toán khác không? (y/n): ").lower()
        if continue_choice != 'y':
            print("Kết thúc chương trình")
            break

if __name__ == "__main__":
    main()
