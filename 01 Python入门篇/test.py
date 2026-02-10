# 定义一个学生类
# 要求：
# 1. 属性包括学生姓名、学号，以及语数英三科的成绩
# 2. 能够设置学生某科目的成绩
# 3. 能够打印出该学生的所有科目成绩
class student:
    def __init__(self, name, student_id, ):
        self.name = name
        self.student_id = student_id
        self.grades = {"语文": 0, "数学": 0, "英语": 0}

    def set_grade(self,score,grade):
        if score in self.grades:
            self.grades[score] = grade


    def print_grade(self):
        print(f"学生{self.name} 学号：{self.student_id}的成绩为：")
        for score in self.grades:
            print(f"{score}: {self.grades[score]}分")

xm = student("小明",20257002)
xm.set_grade('语文',88)
xm.set_grade('数学',66)
xm.print_grade()
