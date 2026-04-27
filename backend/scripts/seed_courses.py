"""导入示例课程数据"""
import asyncio
import uuid

from src.core.database import async_session_factory
from src.models.course import Course
from src.models.student import Student, StudentRole
import hashlib

SAMPLE_COURSES = [
    {
        "course_no": "CS101",
        "name": "计算机科学导论",
        "credit": 3.0,
        "instructor": "张教授",
        "capacity": 100,
        "schedule": [{"day_of_week": 1, "start_period": "1", "end_period": "2", "weeks": list(range(1, 17))}],
        "location": "教学楼A101",
        "campus": "主校区",
        "category": "必修",
        "semester": "2026-Spring",
    },
    {
        "course_no": "CS201",
        "name": "数据结构与算法",
        "credit": 4.0,
        "instructor": "李教授",
        "capacity": 80,
        "schedule": [
            {"day_of_week": 2, "start_period": "3", "end_period": "4", "weeks": list(range(1, 17))},
            {"day_of_week": 4, "start_period": "5", "end_period": "6", "weeks": list(range(1, 17))},
        ],
        "location": "教学楼B202",
        "campus": "主校区",
        "category": "必修",
        "semester": "2026-Spring",
    },
    {
        "course_no": "MATH101",
        "name": "高等数学 I",
        "credit": 5.0,
        "instructor": "王教授",
        "capacity": 150,
        "schedule": [
            {"day_of_week": 1, "start_period": "3", "end_period": "4", "weeks": list(range(1, 17))},
            {"day_of_week": 3, "start_period": "1", "end_period": "2", "weeks": list(range(1, 17))},
        ],
        "location": "教学楼C301",
        "campus": "主校区",
        "category": "必修",
        "semester": "2026-Spring",
    },
    {
        "course_no": "ENG101",
        "name": "大学英语 I",
        "credit": 2.0,
        "instructor": "陈教授",
        "capacity": 60,
        "schedule": [{"day_of_week": 3, "start_period": "5", "end_period": "6", "weeks": list(range(1, 17))}],
        "location": "外语楼101",
        "campus": "东校区",
        "category": "必修",
        "semester": "2026-Spring",
    },
    {
        "course_no": "CS301",
        "name": "机器学习基础",
        "credit": 3.0,
        "instructor": "刘教授",
        "capacity": 50,
        "schedule": [{"day_of_week": 3, "start_period": "5", "end_period": "7", "weeks": list(range(1, 17))}],
        "location": "教学楼A303",
        "campus": "主校区",
        "category": "选修",
        "semester": "2026-Spring",
    },
    {
        "course_no": "PHY101",
        "name": "大学物理",
        "credit": 4.0,
        "instructor": "赵教授",
        "capacity": 120,
        "schedule": [
            {"day_of_week": 2, "start_period": "5", "end_period": "6", "weeks": list(range(1, 17))},
            {"day_of_week": 5, "start_period": "1", "end_period": "2", "weeks": list(range(1, 17))},
        ],
        "location": "物理楼201",
        "campus": "西校区",
        "category": "必修",
        "semester": "2026-Spring",
    },
]


async def seed():
    async with async_session_factory() as session:
        # 创建管理员账户
        admin = Student(
            id=uuid.uuid4(),
            student_no="admin001",
            name="管理员",
            major="教务处",
            grade=0,
            role=StudentRole.ADMIN,
            password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
        )
        session.add(admin)

        # 创建测试学生
        student = Student(
            id=uuid.uuid4(),
            student_no="2024001",
            name="测试学生",
            major="计算机科学",
            grade=2,
            role=StudentRole.STUDENT,
            password_hash=hashlib.sha256("student123".encode()).hexdigest(),
        )
        session.add(student)

        # 导入课程
        for data in SAMPLE_COURSES:
            course = Course(id=uuid.uuid4(), is_active=True, **data)
            session.add(course)

        await session.commit()
        print(f"Seeded: 1 admin, 1 student, {len(SAMPLE_COURSES)} courses")


if __name__ == "__main__":
    asyncio.run(seed())
