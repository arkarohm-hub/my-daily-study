class TreeNode:
    def __init__(self, value):
        self.value = value
        # TODO: Define left and right (initially None)
        self.left = None
        self.right = None

# 1. Create the nodes
root = TreeNode(10)
left_child = TreeNode(5)
right_child = TreeNode(20)

# 2. Connect them
# TODO: Make left_child the left of root
root.left = left_child
# TODO: Make right_child the right of root
# (Write the code here)
root.right = right_child
# 3. Test it
print(f"Root: {root.value}")
if root.left:
    print(f"Left Child: {root.left.value}") 
if root.right:
    print(f"Right Child: {root.right.value}")
else:
    print("Right Child: NOT CONNECTED YET")