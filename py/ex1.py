def Split(x):
	x = x.split(",")
	school = x[0].replace("我是", "")
	print(f"學校:{school}")
	print(f"系級:{x[1]}")
	print(f"姓名:{x[2]}")

# 只有當「直接執行」這個檔案時，才會執行以下程式碼
if __name__ == "__main__":
	Name = "我是靜宜大學,資管二B,林哲旭"
	Split(Name)
