class Browser:
    def __init__(self):
        self.back_stack = []    # Stores history
        self.forward_stack = [] # Stores pages you went back from
        self.current_page = None

    def visit(self, url):
        print(f"Visiting: {url}")
        if self.current_page:
            self.back_stack.append(self.current_page)
        self.current_page = url
        self.forward_stack.clear() # New visit clears forward history

    def back(self):
        # TODO: Logic for clicking "Back"
        # 1. If back_stack is empty, do nothing (print "Cannot go back")
        if not self.back_stack:
            print("Cannot go back")
            return
            
        # 2. Push current_page to forward_stack
        self.forward_stack.append(self.current_page)
        # 3. Pop the top url from back_stack and make it current_page
        self.current_page = self.back_stack.pop()


    def show(self):
        print(f"Current: {self.current_page} | Back: {self.back_stack} | Forward: {self.forward_stack}")

# Test Script
chrome = Browser()
chrome.visit("google.com")
chrome.visit("github.com")
chrome.visit("stackoverflow.com")

print("\n--- Clicking Back ---")
chrome.back() # Should go to github
chrome.show()

print("\n--- Clicking Back ---")
chrome.back() # Should go to google
chrome.show()