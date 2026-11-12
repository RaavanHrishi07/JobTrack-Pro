# JobTrack Pro — Job Application Management System

A desktop-based job application tracker built with Python, Tkinter and SQLite. JobTrack Pro helps you organise applications, track recruitment progress, manage interview dates and analyse your job search activity.

## Features

- **Dashboard:** View total applications, applied, interview and selected counts.
- **Application Management:** Add, edit, view and delete job applications.
- **Search:** Find applications by company, role or location.
- **Status Filters:** Filter applications by Applied, Interview, Selected or Rejected.
- **Sorting:** Sort applications by newest or oldest application date.
- **Interview Scheduling:** Save interview dates and view upcoming interviews.
- **Analytics Dashboard:** Visualise application status distribution and monthly activity.
- **Success Rate:** Calculate the percentage of applications resulting in selection.
- **Response Rate:** Track applications marked as selected or rejected.
- **CSV Export:** Export application records to a CSV file.

## Technologies Used

- Python 3
- Tkinter — GUI
- SQLite — Database
- CSV — Data export
- Matplotlib — Not required; charts are drawn using Tkinter Canvas.

## Project Structure

```text
JobTrack-Pro/
│
├── main.py
├── README.md
├── .gitignore
└── jobtrack.db          # Generated automatically
```

## Requirements

- Python 3.9 or newer
- Windows, macOS or Linux
- No external Python packages are required.

Tkinter and SQLite are included with most standard Python installations.

## Installation and Usage

1. Clone the repository:

```bash
git clone https://github.com/RaavanHrishi07/JobTrack-Pro.git
```

2. Open the project directory:

```bash
cd JobTrack-Pro
```

3. Run the application:

```bash
python main.py
```

The SQLite database is created automatically when the application starts.

## Database

JobTrack Pro uses SQLite for persistent storage. Application records include:

- Company name
- Job role
- Location
- Salary or package
- Application date
- Application status
- Notes
- Interview date

The database is stored locally on your computer.

## CSV Export

Use the **Export CSV** option to save your application records. The exported file can be opened in Microsoft Excel, Google Sheets or other spreadsheet applications.

## Screenshots

Add screenshots of the application dashboard and analytics window here.

## Future Improvements

- Email and desktop interview reminders
- More detailed analytics
- Cloud database integration
- Application document and resume management

## Author

**Hrishikesh Sharma**

GitHub: [RaavanHrishi07](https://github.com/RaavanHrishi07)

## License

This project is licensed under the MIT License.
