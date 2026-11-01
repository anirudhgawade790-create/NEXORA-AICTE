from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='NEXORA AICTE API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'nexora-aicte-backend'}


@app.get('/api/dashboard')
def dashboard():
    return {
        'kpis': [
            {'label': 'Total Applications', 'value': 284, 'change': '+12.4%'} ,
            {'label': 'Pending Applications', 'value': 82, 'change': '+5.2%'} ,
            {'label': 'Under Scrutiny', 'value': 41, 'change': '+3.1%'} ,
            {'label': 'Awaiting EVC', 'value': 18, 'change': '-1.3%'} ,
            {'label': 'Awaiting Committee Review', 'value': 26, 'change': '+2.6%'} ,
            {'label': 'Compliance Due Soon', 'value': 37, 'change': '+9.1%'} ,
            {'label': 'Overdue Cases', 'value': 12, 'change': '-0.7%'} ,
            {'label': 'Expired Documents', 'value': 9, 'change': '+1.4%'} ,
        ],
        'statusDistribution': [
            {'name': 'Submitted', 'value': 72},
            {'name': 'Under Scrutiny', 'value': 54},
            {'name': 'EVC Scheduled', 'value': 38},
            {'name': 'Committee Review', 'value': 52},
            {'name': 'Approved', 'value': 48},
            {'name': 'Returned', 'value': 20},
        ],
        'regionPendency': [
            {'region': 'South', 'value': 64},
            {'region': 'West', 'value': 52},
            {'region': 'North', 'value': 43},
            {'region': 'East', 'value': 39},
            {'region': 'Central', 'value': 31},
        ],
        'monthlyTrend': [
            {'month': 'Jan', 'applications': 34},
            {'month': 'Feb', 'applications': 42},
            {'month': 'Mar', 'applications': 48},
            {'month': 'Apr', 'applications': 60},
            {'month': 'May', 'applications': 57},
            {'month': 'Jun', 'applications': 69},
        ],
        'complianceCompletion': [
            {'name': 'Lease & Land', 'percent': 88},
            {'name': 'Infrastructure', 'percent': 79},
            {'name': 'Undertaking', 'percent': 92},
            {'name': 'Staff & Faculty', 'percent': 74},
        ],
    }


@app.get('/api/applications')
def applications():
    return [
        {
            'id': 'APP-2024-1842',
            'institution': 'Lords Institute of Management',
            'region': 'South',
            'type': 'New Institute',
            'submittedAt': '2024-10-06',
            'stage': 'Initial Scrutiny',
            'officer': 'R. Sharma',
            'daysPending': 13,
            'deadline': '2024-10-19',
            'status': 'Under Review',
            'priority': 'High',
        },
        {
            'id': 'APP-2024-2198',
            'institution': 'Apex College of Engineering',
            'region': 'West',
            'type': 'Extension',
            'submittedAt': '2024-09-18',
            'stage': 'Deficiency Check',
            'officer': 'M. Nair',
            'daysPending': 29,
            'deadline': '2024-10-06',
            'status': 'Deficiency Raised',
            'priority': 'Medium',
        },
        {
            'id': 'APP-2024-1124',
            'institution': 'Blue Horizon School of Design',
            'region': 'North',
            'type': 'Approval',
            'submittedAt': '2024-09-29',
            'stage': 'EVC Scheduling',
            'officer': 'A. Singh',
            'daysPending': 18,
            'deadline': '2024-10-14',
            'status': 'Awaiting EVC',
            'priority': 'High',
        },
    ]


@app.get('/api/compliance')
def compliance():
    return [
        {
            'institution': 'Global Heights Technical Campus',
            'applicationId': 'APP-2024-2021',
            'description': 'Renewed lease validity proof',
            'dueDate': '2024-10-16',
            'status': 'Due Soon',
            'daysRemaining': 6,
            'officer': 'S. Verma',
        },
        {
            'institution': 'Nirmala Polytechnic College',
            'applicationId': 'APP-2024-1437',
            'description': 'Infrastructure compliance evidence',
            'dueDate': '2024-10-04',
            'status': 'Overdue',
            'daysRemaining': -2,
            'officer': 'P. Iyer',
        },
    ]
