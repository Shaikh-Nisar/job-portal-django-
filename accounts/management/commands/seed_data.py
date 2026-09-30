from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from jobs.models import Job, SavedJob
from applications.models import Application


User = get_user_model()


class Command(BaseCommand):
    help = "Create realistic demo data for Job Portal"

    def handle(self, *args, **kwargs):

        self.stdout.write("Creating Job Portal demo data...")

        # -------------------------------------------------
        # DATA
        # -------------------------------------------------

        first_names = [
            "Aarav", "Rahul", "Rohit", "Amit", "Akash",
            "Vikas", "Sagar", "Aditya", "Karan", "Nikhil",
            "Sneha", "Priya", "Pooja", "Neha", "Anjali",
            "Simran", "Riya", "Kavya", "Ayesha", "Shreya",
        ]

        last_names = [
            "Sharma", "Patil", "Khan", "Shaikh", "Jadhav",
            "Verma", "Singh", "Pawar", "Deshmukh", "Gupta",
        ]

        locations = [
            "Hyderabad",
            "Pune",
            "Mumbai",
            "Bangalore",
            "Delhi",
            "Chennai",
            "Noida",
            "Gurgaon",
            "Ahmedabad",
            "Nashik",
        ]

        job_data = [
            ("Python Developer", "Python, Django, REST API, MySQL"),
            ("Django Developer", "Python, Django, MySQL, REST API"),
            ("Full Stack Developer", "Python, Django, HTML, CSS, JavaScript"),
            ("Backend Developer", "Python, Django, PostgreSQL, REST API"),
            ("Data Analyst", "Python, SQL, Power BI, Excel"),
            ("Data Analytics", "Python, SQL, Power BI, Pandas"),
            ("Java Developer", "Java, Spring Boot, MySQL, REST API"),
            ("Software Engineer", "Python, Java, SQL, Git"),
            ("Frontend Developer", "HTML, CSS, JavaScript, Bootstrap"),
            ("Machine Learning Engineer", "Python, Machine Learning, Pandas"),
            ("QA Engineer", "Selenium, Python, SQL, Testing"),
            ("Web Developer", "HTML, CSS, JavaScript, Django"),
            ("API Developer", "Python, Django REST Framework, MySQL"),
            ("Junior Python Developer", "Python, Django, SQL"),
            ("Associate Software Engineer", "Python, Java, SQL, Git"),
        ]

        companies = [
            "TechNova Solutions",
            "CodeSphere Technologies",
            "InnoSoft Systems",
            "NextGen IT Solutions",
            "BlueWave Technologies",
            "CloudMatrix Pvt Ltd",
            "DataVision Analytics",
            "SmartCode Solutions",
            "Vertex Infotech",
            "DigitalCore Systems",
        ]

        # -------------------------------------------------
        # RECRUITERS
        # -------------------------------------------------

        recruiters = []

        for i, company_name in enumerate(companies, start=1):

            username = f"recruiter{i}"

            recruiter, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"recruiter{i}@jobportal.demo",
                    "role": "recruiter",
                    "first_name": "Recruiter",
                    "last_name": str(i),
                }
            )

            if created:
                recruiter.set_password("Recruiter@123")
                recruiter.save()

            recruiters.append(recruiter)

        self.stdout.write(
            self.style.SUCCESS(
                f"Recruiters ready: {len(recruiters)}"
            )
        )

        # -------------------------------------------------
        # CANDIDATES
        # -------------------------------------------------

        candidates = []

        for i in range(1, 51):

            first = first_names[(i - 1) % len(first_names)]
            last = last_names[(i - 1) % len(last_names)]

            username = f"candidate{i}"

            candidate, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"candidate{i}@jobportal.demo",
                    "role": "candidate",
                    "first_name": first,
                    "last_name": last,
                    "phone": f"900000{i:04d}",
                    "skills": random.choice([
                        "Python, Django, MySQL",
                        "Python, SQL, Power BI",
                        "Java, Spring Boot, MySQL",
                        "HTML, CSS, JavaScript",
                        "Python, Machine Learning, Pandas",
                        "Django, REST API, Git",
                    ]),
                    "education": random.choice([
                        "MCA",
                        "BCA",
                        "BSc Computer Science",
                        "BE Computer Engineering",
                        "BTech Computer Science",
                    ]),
                }
            )

            if created:
                candidate.set_password("Candidate@123")
                candidate.save()

            candidates.append(candidate)

        self.stdout.write(
            self.style.SUCCESS(
                f"Candidates ready: {len(candidates)}"
            )
        )

        # -------------------------------------------------
        # JOBS
        # -------------------------------------------------

        jobs = []

        for i in range(1, 51):

            title, skills = random.choice(job_data)
            recruiter = random.choice(recruiters)
            company = random.choice(companies)
            location = random.choice(locations)

            job = Job.objects.create(
                title=title,
                company_name=company,
                location=location,
                salary_min=random.choice([
                    25000, 30000, 35000, 40000, 45000
                ]),
                salary_max=random.choice([
                    60000, 70000, 80000, 90000, 120000
                ]),
                job_type=random.choice([
                    "full_time",
                    "full_time",
                    "full_time",
                    "part_time",
                    "internship",
                    "contract",
                ]),
                experience=random.choice([
                    "0-1 Years",
                    "1-2 Years",
                    "2-3 Years",
                    "3-5 Years",
                ]),
                skills=skills,
                description=(
                    f"We are looking for a {title} to join our "
                    f"growing technology team. The candidate will "
                    f"work on real-world software projects."
                ),
                vacancies=random.randint(1, 6),
                application_deadline=(
                    timezone.now().date() +
                    timedelta(days=random.randint(15, 90))
                ),
                recruiter=recruiter,
                is_active=random.choice([True, True, True, False]),
            )

            jobs.append(job)

        self.stdout.write(
            self.style.SUCCESS(
                f"Jobs created: {len(jobs)}"
            )
        )

        # -------------------------------------------------
        # APPLICATIONS
        # -------------------------------------------------

        statuses = [
            "applied",
            "applied",
            "applied",
            "shortlisted",
            "shortlisted",
            "rejected",
            "selected",
        ]

        application_count = 0

        for job in jobs:

            # Every job gets several applications
            selected_candidates = random.sample(
                candidates,
                random.randint(3, 10)
            )

            for candidate in selected_candidates:

                if Application.objects.filter(
                    job=job,
                    candidate=candidate
                ).exists():
                    continue

                Application.objects.create(
                    job=job,
                    candidate=candidate,
                    cover_letter=(
                        f"I am interested in the {job.title} position "
                        f"and believe my technical skills match this role."
                    ),
                    status=random.choice(statuses),
                )

                application_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Applications created: {application_count}"
            )
        )

        # -------------------------------------------------
        # SAVED JOBS
        # -------------------------------------------------

        saved_count = 0

        for candidate in candidates:

            selected_jobs = random.sample(
                jobs,
                random.randint(1, 5)
            )

            for job in selected_jobs:

                if SavedJob.objects.filter(
                    candidate=candidate,
                    job=job
                ).exists():
                    continue

                SavedJob.objects.create(
                    candidate=candidate,
                    job=job
                )

                saved_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Saved jobs created: {saved_count}"
            )
        )

        # -------------------------------------------------
        # COMPLETE
        # -------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "JOB PORTAL DEMO DATA CREATED SUCCESSFULLY"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )