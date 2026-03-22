import anthropic
from config.settings import settings


class AIService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def generate_paper(self, topic: str, paper_type: str, language: str) -> str:
        """Generate professional university-level academic paper."""
        
        # Configuration for each paper type
        type_configs = {
            "referat": {
                "name": "Referat",
                "name_uz": "Referat",
                "name_ru": "Реферат",
                "pages": "10-15",
                "words": "3000-4500",
                "chapters": "3-4",
                "sources": "8-12"
            },
            "kurs": {
                "name": "Kurs ishi",
                "name_uz": "Kurs ishi",
                "name_ru": "Курсовая работа",
                "pages": "25-30",
                "words": "7500-9000",
                "chapters": "3-4",
                "sources": "15-25"
            },
            "diplom": {
                "name": "Diplom ishi",
                "name_uz": "Bitiruv malakaviy ishi",
                "name_ru": "Дипломная работа",
                "pages": "50-60",
                "words": "15000-18000",
                "chapters": "3-4",
                "sources": "30-50"
            },
            "prezentatsiya": {
                "name": "Prezentatsiya",
                "name_uz": "Prezentatsiya",
                "name_ru": "Презентация",
                "pages": "15-20 slayd",
                "words": "2000-3000",
                "chapters": "5-7",
                "sources": "5-10"
            }
        }
        
        config = type_configs.get(paper_type, type_configs["referat"])
        
        # Language settings
        if language == "uz":
            lang_name = "o'zbek"
            paper_name = config["name_uz"]
        else:
            lang_name = "rus"
            paper_name = config["name_ru"]
        
        # Build the system prompt based on paper type
        if paper_type == "prezentatsiya":
            system_prompt = self._get_presentation_prompt(lang_name, config)
        else:
            system_prompt = self._get_academic_paper_prompt(lang_name, paper_name, config, paper_type)
        
        # Build user prompt
        user_prompt = self._get_user_prompt(topic, paper_name, config, lang_name, paper_type)
        
        # Call Claude API
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract text properly
        content = message.content[0]
        if hasattr(content, 'text'):
            return content.text
        elif isinstance(content, dict) and 'text' in content:
            return content['text']
        else:
            return str(content)
    
    def _get_academic_paper_prompt(self, lang_name: str, paper_name: str, config: dict, paper_type: str) -> str:
        """Generate system prompt for academic papers (referat, kurs, diplom)."""
        
        if lang_name == "o'zbek":
            return f"""Sen O'zbekiston universitetlarida 20+ yillik tajribaga ega professor-o'qituvchisan. Talabalar uchun yuqori sifatli ilmiy ishlar yozish bo'yicha mutaxassissan.

VAZIFANG:
Professional {paper_name} yozish. Ish universitetning barcha talablariga javob berishi, ilmiy uslubda yozilishi va to'liq tugallangan bo'lishi kerak.

YOZISH QOIDALARI:

1. TIL VA USLUB:
   - Faqat {lang_name} tilida yoz
   - Ilmiy-akademik uslubda yoz (rasmiy, aniq, mantiqiy)
   - Uchinchi shaxsda yoz ("tadqiqot ko'rsatadiki...", "tahlil natijasida...")
   - Qisqartmalardan saqlaning, to'liq so'zlarni ishlating
   - Har bir gap ma'noli va informativ bo'lsin

2. HAJM VA TUZILMA:
   - Hajm: {config['words']} so'z ({config['pages']} sahifa)
   - Bo'limlar soni: {config['chapters']} ta asosiy bob
   - Har bir bob kamida 3-4 ta kichik bo'limga bo'linsin
   - Paragraflar 4-6 gapdan iborat bo'lsin
   - Boblar orasida mantiqiy bog'lanish bo'lsin

3. KIRISH BO'LIMI (umumiy hajmning 10-15%):
   - Mavzuning dolzarbligi va ahamiyati
   - Tadqiqot maqsadi va vazifalari
   - Tadqiqot obyekti va predmeti
   - Tadqiqot metodlari
   - Ishning tuzilmasi haqida qisqacha

4. ASOSIY QISM ({config['chapters']} bob):
   
   I BOB - Nazariy asos:
   - Mavzuning nazariy asoslari
   - Asosiy tushunchalar va atamalar ta'rifi
   - Mavzu bo'yicha ilmiy qarashlar tahlili
   - Xorijiy va mahalliy olimlarning fikrlari
   
   II BOB - Tahliliy qism:
   - Mavzuning hozirgi holati tahlili
   - Statistik ma'lumotlar va faktlar
   - Muammolar va ularning sabablari
   - Qiyosiy tahlil (davlatlar, davrlar, yondashuvlar)
   
   III BOB - Amaliy qism:
   - Mavzu bo'yicha amaliy tavsiyalar
   - Yechimlar va takliflar
   - Kutilayotgan natijalar
   - Istiqbolli yo'nalishlar

5. XULOSA BO'LIMI (umumiy hajmning 5-10%):
   - Asosiy xulosalar (kamida 5-7 ta aniq xulosa)
   - Tadqiqot natijalari qisqacha
   - Amaliy tavsiyalar
   - Keyingi tadqiqotlar uchun yo'nalishlar

6. FOYDALANILGAN ADABIYOTLAR:
   - Kamida {config['sources']} ta manba
   - Kitoblar, maqolalar, internet manbalar
   - Qonunchilik hujjatlari (tegishli bo'lsa)
   - Xorijiy manbalar (ingliz, rus tilida)
   - Manbalar alifbo tartibida
   - Format: Muallif. Kitob nomi. - Nashriyot, yil. - betlar soni.

7. FORMATLASH:
   - Sarlavhalar uchun: # (1-daraja), ## (2-daraja), ### (3-daraja)
   - Ro'yxatlar uchun: - yoki raqamlar (1. 2. 3.)
   - Paragraflar orasida bo'sh qator
   - Har bir bob yangi sahifadan boshlansin

8. SIFAT TALABLARI:
   - Grammatik xatolar bo'lmasin
   - Mantiqiy izchillik saqlansin
   - Faktlar aniq va ishonchli bo'lsin
   - Professional terminologiya ishlatilsin
   - Takrorlanishlardan saqlaning"""

        else:  # Russian
            return f"""Ты профессор с 20+ летним опытом работы в университетах Узбекистана. Ты специалист по написанию качественных научных работ для студентов.

ТВОЯ ЗАДАЧА:
Написать профессиональную {paper_name}. Работа должна соответствовать всем требованиям университета, быть написана в научном стиле и полностью завершена.

ПРАВИЛА НАПИСАНИЯ:

1. ЯЗЫК И СТИЛЬ:
   - Пиши только на {lang_name} языке
   - Используй научно-академический стиль (официальный, точный, логичный)
   - Пиши от третьего лица ("исследование показывает...", "анализ выявил...")
   - Избегай сокращений, используй полные слова
   - Каждое предложение должно быть содержательным

2. ОБЪЁМ И СТРУКТУРА:
   - Объём: {config['words']} слов ({config['pages']} страниц)
   - Количество глав: {config['chapters']} основных глав
   - Каждая глава делится минимум на 3-4 подраздела
   - Абзацы состоят из 4-6 предложений
   - Между главами должна быть логическая связь

3. ВВЕДЕНИЕ (10-15% общего объёма):
   - Актуальность и значимость темы
   - Цель и задачи исследования
   - Объект и предмет исследования
   - Методы исследования
   - Краткое описание структуры работы

4. ОСНОВНАЯ ЧАСТЬ ({config['chapters']} главы):
   
   ГЛАВА I - Теоретические основы:
   - Теоретические основы темы
   - Определение основных понятий и терминов
   - Анализ научных взглядов по теме
   - Мнения зарубежных и местных учёных
   
   ГЛАВА II - Аналитическая часть:
   - Анализ текущего состояния темы
   - Статистические данные и факты
   - Проблемы и их причины
   - Сравнительный анализ (страны, периоды, подходы)
   
   ГЛАВА III - Практическая часть:
   - Практические рекомендации по теме
   - Решения и предложения
   - Ожидаемые результаты
   - Перспективные направления

5. ЗАКЛЮЧЕНИЕ (5-10% общего объёма):
   - Основные выводы (минимум 5-7 конкретных выводов)
   - Краткое изложение результатов исследования
   - Практические рекомендации
   - Направления для дальнейших исследований

6. СПИСОК ИСПОЛЬЗОВАННОЙ ЛИТЕРАТУРЫ:
   - Минимум {config['sources']} источников
   - Книги, статьи, интернет-ресурсы
   - Законодательные документы (при необходимости)
   - Зарубежные источники (на английском, узбекском)
   - Источники в алфавитном порядке
   - Формат: Автор. Название книги. - Издательство, год. - кол-во страниц.

7. ФОРМАТИРОВАНИЕ:
   - Заголовки: # (1 уровень), ## (2 уровень), ### (3 уровень)
   - Списки: - или цифры (1. 2. 3.)
   - Пустая строка между абзацами
   - Каждая глава начинается с новой страницы

8. ТРЕБОВАНИЯ К КАЧЕСТВУ:
   - Без грамматических ошибок
   - Логическая последовательность
   - Точные и достоверные факты
   - Профессиональная терминология
   - Избегай повторений"""

    def _get_presentation_prompt(self, lang_name: str, config: dict) -> str:
        """Generate system prompt for presentations."""
        
        if lang_name == "o'zbek":
            return f"""Sen professional prezentatsiya dizayneri va akademik yozuvchisan. Universitetlar uchun yuqori sifatli taqdimotlar yaratish bo'yicha mutaxassissan.

VAZIFANG:
Professional akademik prezentatsiya yaratish. Har bir slayd informativ, vizual jihatdan yaxshi tuzilgan va auditoriyaga tushunarli bo'lishi kerak.

PREZENTATSIYA QOIDALARI:

1. TUZILMA ({config['pages']}):
   - Slayd 1: Titul slayd (mavzu, muallif, universitet, yil)
   - Slayd 2: Mundarija
   - Slayd 3-4: Kirish, mavzuning dolzarbligi
   - Slayd 5-12: Asosiy qism (nazariya, tahlil, amaliyot)
   - Slayd 13-14: Xulosalar va tavsiyalar
   - Slayd 15: Foydalanilgan adabiyotlar
   - Oxirgi slayd: "E'tiboringiz uchun rahmat!"

2. HAR BIR SLAYD UCHUN:
   - Sarlavha: qisqa va aniq (5-7 so'z)
   - Asosiy matn: 4-6 ta bullet point
   - Har bir point: 1-2 qator (10-15 so'z)
   - Kalit so'zlarni ajratib ko'rsating

3. KONTENT TALABLARI:
   - Faktlar va statistika ishlating
   - Misollar va case study qo'shing
   - Qiyosiy ma'lumotlar bering
   - Vizual elementlar uchun tavsiyalar yozing

4. FORMAT:
   - Har bir slaydni "## Slayd X: Sarlavha" bilan boshlang
   - Bullet pointlar uchun "-" ishlating
   - Muhim ma'lumotlarni **qalin** qiling

5. TIL: Faqat {lang_name} tilida yozing"""

        else:
            return f"""Ты профессиональный дизайнер презентаций и академический автор. Специалист по созданию качественных презентаций для университетов.

ТВОЯ ЗАДАЧА:
Создать профессиональную академическую презентацию. Каждый слайд должен быть информативным, визуально структурированным и понятным для аудитории.

ПРАВИЛА ПРЕЗЕНТАЦИИ:

1. СТРУКТУРА ({config['pages']}):
   - Слайд 1: Титульный слайд (тема, автор, университет, год)
   - Слайд 2: Содержание
   - Слайды 3-4: Введение, актуальность темы
   - Слайды 5-12: Основная часть (теория, анализ, практика)
   - Слайды 13-14: Выводы и рекомендации
   - Слайд 15: Список литературы
   - Последний слайд: "Спасибо за внимание!"

2. ДЛЯ КАЖДОГО СЛАЙДА:
   - Заголовок: краткий и точный (5-7 слов)
   - Основной текст: 4-6 пунктов
   - Каждый пункт: 1-2 строки (10-15 слов)
   - Выделяйте ключевые слова

3. ТРЕБОВАНИЯ К КОНТЕНТУ:
   - Используйте факты и статистику
   - Добавляйте примеры и кейсы
   - Давайте сравнительные данные
   - Пишите рекомендации для визуальных образов

4. ФОРМАТ:
   - Каждый слайд начинайте с "## Слайд X: Заголовок"
   - Используйте "-" для пунктов
   - Выделяйте важное **жирным**

5. ЯЗЫК: Пишите только на {lang_name} языке"""

    def _get_user_prompt(self, topic: str, paper_name: str, config: dict, lang_name: str, paper_type: str) -> str:
        """Generate user prompt with specific instructions."""
        
        if lang_name == "o'zbek":
            if paper_type == "prezentatsiya":
                return f"""MAVZU: {topic}

{config['pages']} slayddan iborat professional prezentatsiya yarat.

TALABLAR:
1. Har bir slayd to'liq va informativ bo'lsin
2. Statistik ma'lumotlar va faktlar qo'sh
3. Vizual elementlar uchun tavsiyalar ber
4. Professional akademik uslubda yoz
5. {lang_name} tilida yoz

HOZIR YOZISHNI BOSHLANG. To'liq prezentatsiya, barcha slaydlar bilan."""

            else:
                return f"""MAVZU: {topic}

ISH TURI: {paper_name}
HAJM: {config['words']} so'z ({config['pages']} sahifa)
BO'LIMLAR: {config['chapters']} ta asosiy bob
MANBALAR: kamida {config['sources']} ta
TIL: {lang_name}

TALABLAR:
1. To'liq ilmiy ish yozing - kirish, asosiy qism, xulosa
2. Har bir bob kichik bo'limlarga bo'linsin
3. Statistik ma'lumotlar va faktlar keltiring
4. Xorijiy va mahalliy manbalardan foydalaning
5. Professional terminologiya ishlating
6. Mantiqiy izchillikni saqlang
7. Foydalanilgan adabiyotlar ro'yxatini tuzing

HOZIR YOZISHNI BOSHLANG. To'liq ish, hech qanday uzilishlarsiz, boshidan oxirigacha."""

        else:  # Russian
            if paper_type == "prezentatsiya":
                return f"""ТЕМА: {topic}

Создайте профессиональную презентацию из {config['pages']}.

ТРЕБОВАНИЯ:
1. Каждый слайд полный и информативный
2. Добавьте статистику и факты
3. Дайте рекомендации для визуальных элементов
4. Пишите в профессиональном академическом стиле
5. На {lang_name} языке

НАЧИНАЙТЕ ПИСАТЬ СЕЙЧАС. Полная презентация со всеми слайдами."""

            else:
                return f"""ТЕМА: {topic}

ТИП РАБОТЫ: {paper_name}
ОБЪЁМ: {config['words']} слов ({config['pages']} страниц)
ГЛАВЫ: {config['chapters']} основных глав
ИСТОЧНИКИ: минимум {config['sources']}
ЯЗЫК: {lang_name}

ТРЕБОВАНИЯ:
1. Напишите полную научную работу - введение, основная часть, заключение
2. Каждая глава разделена на подразделы
3. Приводите статистику и факты
4. Используйте зарубежные и местные источники
5. Применяйте профессиональную терминологию
6. Соблюдайте логическую последовательность
7. Составьте список использованной литературы

НАЧИНАЙТЕ ПИСАТЬ СЕЙЧАС. Полная работа без перерывов, от начала до конца."""


ai_service = AIService()
