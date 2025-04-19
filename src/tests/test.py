"""
Test Runner for Pathfinding Algorithms
-------------------------------------
This script provides an interface to run tests for different pathfinding algorithms:
- A* (A-Star)
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- UCS (Uniform Cost Search)

User can select which algorithm test to run via a console menu.
"""

import os
import sys
import importlib
import time

def clear_screen():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Prints the program header."""
    clear_screen()
    print("=" * 70)
    print("               PATHFINDING ALGORITHM TEST RUNNER                  ")
    print("=" * 70)
    print("\nChọn một thuật toán để chạy kiểm thử:")
    print("-" * 70)

def print_menu():
    """Prints the menu of available algorithm tests."""
    print("1. A* (A-Star) - Thuật toán tìm đường đi tối ưu với heuristic")
    print("2. BFS (Breadth-First Search) - Thuật toán tìm kiếm theo chiều rộng")
    print("3. DFS (Depth-First Search) - Thuật toán tìm kiếm theo chiều sâu") 
    print("4. UCS (Uniform Cost Search) - Thuật toán tìm kiếm theo chi phí đồng nhất")
    print("\n0. Thoát")
    print("-" * 70)

def run_test(module_name):
    """
    Runs the specified test module.
    
    Args:
        module_name (str): Name of the module to run.
    """
    print(f"\nĐang khởi chạy thuật toán {module_name}...")
    print("Bạn có thể tắt cửa sổ pygame để kết thúc kiểm thử")
    time.sleep(2)
    
    # Add parent directory to path to ensure imports work correctly
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    try:
        # Import and run the selected module
        module = importlib.import_module(f"src.tests.{module_name}")
        if hasattr(module, 'main'):
            module.main()
        else:
            print(f"Lỗi: Module {module_name} không có hàm main().")
    except ImportError as e:
        print(f"Lỗi: Không thể import module {module_name}.")
        print(f"Chi tiết lỗi: {e}")
    except Exception as e:
        print(f"Lỗi khi chạy {module_name}: {e}")
    
    print(f"\n Nội dung test đã được xuất thành file {module_name}.csv")

    input("\nNhấn Enter để trở về menu chính...")

def main():
    """Main program function."""
    while True:
        print_header()
        print_menu()
        
        # Get user choice
        try:
            choice = input("\nNhập lựa chọn của bạn (0-4): ").strip()
            
            if choice == '0':
                print("\nCảm ơn bạn đã sử dụng chương trình. Tạm biệt!")
                break
                
            elif choice == '1':
                run_test("test_a_star")
                
            elif choice == '2':
                run_test("test_bfs")
                
            elif choice == '3':
                run_test("test_dfs")
                
            elif choice == '4':
                run_test("test_ucs")
                
            else:
                print("\nLựa chọn không hợp lệ. Vui lòng chọn từ 0-4.")
                time.sleep(1.5)
                
        except KeyboardInterrupt:
            print("\n\nChương trình bị ngắt. Tạm biệt!")
            break
        except Exception as e:
            print(f"\nĐã xảy ra lỗi: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()