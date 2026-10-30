"""증상 카테고리 → 연결 진료과 (requirements 4. 증상 카테고리, H-1). 진료과 코드는 departments 와 같다."""

CATEGORIES = [
    {"code": "cold", "name": "감기·몸살", "departments": ["01", "23", "13"]},
    {"code": "rhinitis", "name": "비염", "departments": ["13"]},
    {"code": "stomach", "name": "위장장애", "departments": ["01"]},
    {"code": "chronic", "name": "당뇨·고혈압", "departments": ["01", "23"]},
    {"code": "skin", "name": "피부질환", "departments": ["14"]},
    {"code": "acne", "name": "여드름", "departments": ["14"]},
    {"code": "hair", "name": "탈모", "departments": ["14"]},
    {"code": "eye", "name": "안구질환", "departments": ["12"]},
    {"code": "pain", "name": "통증·관절", "departments": ["05", "21"]},
    {"code": "kids", "name": "소아", "departments": ["11"]},
    {"code": "mood", "name": "우울·불안", "departments": ["03"]},
    {"code": "sleep", "name": "불면증", "departments": ["03", "23"]},
]

CATEGORY_BY_CODE = {c["code"]: c for c in CATEGORIES}
