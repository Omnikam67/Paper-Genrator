// Configuration
const YEARS = ['1st Year', '2nd Year', '3rd Year', '4th Year'];
const SEMESTERS = [];
const YEAR_TO_SEMESTERS = {
    '1st Year': ['1st Sem', '2nd Sem'],
    '2nd Year': ['3rd Sem', '4th Sem'],
    '3rd Year': ['5th Sem', '6th Sem'],
    '4th Year': ['7th Sem', '8th Sem']
};
const SUBJECTS = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'History'];
const CHAPTERS = ['Chapter 1', 'Chapter 2', 'Chapter 3', 'Chapter 4', 'Chapter 5'];
const QUESTION_TYPES = ['MCQ', 'One Sentence', 'Long Answer'];
const EXAM_TYPES = ['MSE', 'ESE', 'Class Test'];

const SUBJECTS_BY_YEAR_SEM = {
    '2nd Year': {
        '3rd Sem': [
            'Python(PM)',
            'DSA(Data Structure and algorithum)',
            'OE(Open Elective)',
            'IOT(Internate of things)',
            'EE(Engenering Economics)',
            'EIT(Ethics in it)'
        ]
    }
};

const CHAPTERS_BY_SUBJECT = {
    'Python(PM)': [
        'Introduction to Python',
        'Python Fundamentals',
        'Data Structures in Python',
        'Functions, Modules & Packages',
        'Object Oriented Programming',
        'Python Libraries & Frameworks'
    ],
    'DSA(Data Structure and algorithum)': [
        'Introduction to Data Structures',
        'Arrays',
        'Linked Lists',
        'Stack',
        'Queues',
        'Trees & Graphs'
    ],
    'EE(Engenering Economics)': [
        'Definition and Scope of Engineering Economics',
        'Theory of Production',
        'Time value of Money'
    ],
    'EIT(Ethics in it)': [
        'Introduction to Ethics',
        'Ethics in information Technology',
        'Intellectual Property Rights and Computer Technology'
    ]
};

function getSubjects(year, semester) {
    const map = SUBJECTS_BY_YEAR_SEM[year];
    if (map && map[semester]) return map[semester];
    return SUBJECTS;
}

let currentStep = {
    add: 'year',
    generate: 'year'
};

let selectedData = {
    year: '',
    semester: '',
    subject: '',
    chapter: '',
    questionType: '',
    courseCode: '',
    examTime: 60,
    examType: '',
    selectedChapters: [],
    globalDistribution: {}
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    initializeOptions();
});

function initializeOptions() {
    // Add Question Form Options
    renderOptions('yearOptions', YEARS, (year) => {
        selectedData.year = year;
        renderOptions('semesterOptions', YEAR_TO_SEMESTERS[year] || [], (semester) => {
            selectedData.semester = semester;
            renderOptions('subjectOptions', getSubjects(year, semester), (subject) => {
                selectedData.subject = subject;
                currentStep.add = 'chapter';
                loadChapters(subject);
                showStep('add');
            });
            currentStep.add = 'subject';
            showStep('add');
        });
        currentStep.add = 'semester';
        showStep('add');
    });

    renderOptions('semesterOptions', SEMESTERS, (semester) => {
        selectedData.semester = semester;
        currentStep.add = 'subject';
        showStep('add');
    });

    renderOptions('subjectOptions', SUBJECTS, (subject) => {
        selectedData.subject = subject;
        currentStep.add = 'chapter';
        loadChapters(subject);
        showStep('add');
    });

    renderOptions('typeOptions', QUESTION_TYPES, (type) => {
        selectedData.questionType = type;
        currentStep.add = 'details';
        if (type === 'MCQ') {
            document.getElementById('mcqSection').style.display = 'block';
        } else {
            document.getElementById('mcqSection').style.display = 'none';
        }
        showStep('add');
    });

    // Generate Paper Form Options
    renderOptions('genYearOptions', YEARS, (year) => {
        selectedData.year = year;
        renderOptions('genSemesterOptions', YEAR_TO_SEMESTERS[year] || [], (semester) => {
            selectedData.semester = semester;
            renderOptions('genSubjectOptions', getSubjects(year, semester), (subject) => {
                selectedData.subject = subject;
                currentStep.generate = 'courseCode';
                loadChaptersForGeneration(subject);
                showStep('generate');
            });
            currentStep.generate = 'subject';
            showStep('generate');
        });
        currentStep.generate = 'semester';
        showStep('generate');
    });

    renderOptions('genSemesterOptions', SEMESTERS, (semester) => {
        selectedData.semester = semester;
        currentStep.generate = 'subject';
        showStep('generate');
    });

    renderOptions('genSubjectOptions', SUBJECTS, (subject) => {
        selectedData.subject = subject;
        currentStep.generate = 'courseCode';
        loadChaptersForGeneration(subject);
        showStep('generate');
    });

    renderOptions('examTypeOptions', EXAM_TYPES, (type) => {
        selectedData.examType = type;
        selectedData.selectedChapters = []; // Reset selected chapters
        currentStep.generate = 'chapters';

        // Reload chapters with new exam type logic
        loadChaptersForGeneration(selectedData.subject);

        // Auto-select all chapters for ESE
        if (type === 'ESE') {
            setTimeout(() => {
                const allCheckboxes = document.querySelectorAll('.chapter-checkbox');
                allCheckboxes.forEach(cb => {
                    cb.checked = true;
                    if (!selectedData.selectedChapters.includes(cb.value)) {
                        selectedData.selectedChapters.push(cb.value);
                    }
                });
            }, 100);
        }

        showStep('generate');
    });
}

function renderOptions(containerId, options, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';
    options.forEach(option => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'option-btn';
        btn.textContent = option;
        btn.onclick = () => {
            document.querySelectorAll(`#${containerId} .option-btn`).forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            callback(option);
        };
        container.appendChild(btn);
    });
}

function loadChapters(subject) {
    const chapterSelect = document.getElementById('chapterSelect');
    chapterSelect.innerHTML = '<option value="">-- Select Chapter --</option>';

    // Use subject-specific chapters if available, otherwise use default chapters
    const chapters = CHAPTERS_BY_SUBJECT[subject] || CHAPTERS;

    chapters.forEach(chapter => {
        const option = document.createElement('option');
        option.value = chapter;
        option.textContent = chapter;
        chapterSelect.appendChild(option);
    });
}

function updateChapter() {
    const chapterSelect = document.getElementById('chapterSelect');
    selectedData.chapter = chapterSelect.value;
    if (selectedData.chapter) {
        currentStep.add = 'type';
        showStep('add');
    }
}

function loadChaptersForGeneration(subject) {
    const chapterCheckboxes = document.getElementById('chapterCheckboxes');
    const chaptersLabel = document.getElementById('chaptersLabel');
    chapterCheckboxes.innerHTML = '';

    // Update label based on exam type
    const examType = selectedData.examType;
    if (examType === 'MSE') {
        chaptersLabel.textContent = 'Select Any 3 Chapters (MSE)';
        chaptersLabel.style.color = '#2563eb';
    } else if (examType === 'ESE') {
        chaptersLabel.textContent = 'All Chapters Selected (ESE)';
        chaptersLabel.style.color = '#059669';
    } else {
        chaptersLabel.textContent = 'Select Chapter(s) (Class Test)';
        chaptersLabel.style.color = '#555';
    }

    // Use subject-specific chapters if available, otherwise use default chapters
    const chapters = CHAPTERS_BY_SUBJECT[subject] || CHAPTERS;

    chapters.forEach(chapter => {
        const label = document.createElement('label');
        label.style.display = 'flex';
        label.style.alignItems = 'center';
        label.style.gap = '10px';
        label.style.cursor = 'pointer';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = chapter;
        checkbox.className = 'chapter-checkbox';
        checkbox.onchange = () => handleChapterSelection(checkbox, chapter);

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(chapter));
        chapterCheckboxes.appendChild(label);
    });
}

function handleChapterSelection(checkbox, chapter) {
    const examType = selectedData.examType;
    const allCheckboxes = document.querySelectorAll('.chapter-checkbox');

    if (examType === 'MSE') {
        // MSE: Allow only 3 chapters
        if (checkbox.checked) {
            if (selectedData.selectedChapters.length >= 3) {
                checkbox.checked = false;
                showMessage('paperMessage', 'MSE allows only 3 chapters', 'error');
                return;
            }
            selectedData.selectedChapters.push(chapter);
        } else {
            selectedData.selectedChapters = selectedData.selectedChapters.filter(c => c !== chapter);
        }
    } else if (examType === 'ESE') {
        // ESE: Select all chapters automatically
        if (checkbox.checked) {
            // Select all chapters
            selectedData.selectedChapters = [];
            allCheckboxes.forEach(cb => {
                cb.checked = true;
                if (!selectedData.selectedChapters.includes(cb.value)) {
                    selectedData.selectedChapters.push(cb.value);
                }
            });
            showMessage('paperMessage', 'ESE requires all chapters to be selected', 'success');
        } else {
            // Prevent unchecking for ESE
            checkbox.checked = true;
            showMessage('paperMessage', 'ESE requires all chapters', 'error');
        }
    } else {
        // Class Test: Free selection
        if (checkbox.checked) {
            if (!selectedData.selectedChapters.includes(chapter)) {
                selectedData.selectedChapters.push(chapter);
            }
        } else {
            selectedData.selectedChapters = selectedData.selectedChapters.filter(c => c !== chapter);
        }
    }
}

function showStep(form) {
    const step = form === 'add' ? currentStep.add : currentStep.generate;
    const prefix = form === 'add' ? '' : 'gen';

    // Hide all steps
    if (form === 'add') {
        document.getElementById('yearStep').style.display = 'none';
        document.getElementById('semesterStep').style.display = 'none';
        document.getElementById('subjectStep').style.display = 'none';
        document.getElementById('chapterStep').style.display = 'none';
        document.getElementById('typeStep').style.display = 'none';
        document.getElementById('questionDetailsStep').style.display = 'none';

        // Update step indicator
        document.getElementById('stepIndicator').textContent = `Step: ${step.toUpperCase()}`;
    } else {
        document.getElementById('genYearStep').style.display = 'none';
        document.getElementById('genSemesterStep').style.display = 'none';
        document.getElementById('genSubjectStep').style.display = 'none';
        document.getElementById('courseCodeStep').style.display = 'none';
        document.getElementById('timeStep').style.display = 'none';
        document.getElementById('examTypeStep').style.display = 'none';
        document.getElementById('chaptersStep').style.display = 'none';
        document.getElementById('questionDistributionStep').style.display = 'none';
        document.getElementById('genPaperBtn').style.display = 'none';

        // Update step indicator
        document.getElementById('paperStepIndicator').textContent = `Step: ${step.toUpperCase()}`;
    }

    // Show current step
    if (form === 'add') {
        if (step === 'year') document.getElementById('yearStep').style.display = 'block';
        if (step === 'semester') document.getElementById('semesterStep').style.display = 'block';
        if (step === 'subject') document.getElementById('subjectStep').style.display = 'block';
        if (step === 'chapter') document.getElementById('chapterStep').style.display = 'block';
        if (step === 'type') document.getElementById('typeStep').style.display = 'block';
        if (step === 'details') document.getElementById('questionDetailsStep').style.display = 'block';
    } else {
        if (step === 'year') document.getElementById('genYearStep').style.display = 'block';
        if (step === 'semester') document.getElementById('genSemesterStep').style.display = 'block';
        if (step === 'subject') document.getElementById('genSubjectStep').style.display = 'block';
        if (step === 'courseCode') document.getElementById('courseCodeStep').style.display = 'block';
        if (step === 'time') document.getElementById('timeStep').style.display = 'block';
        if (step === 'examType') document.getElementById('examTypeStep').style.display = 'block';
        if (step === 'chapters') document.getElementById('chaptersStep').style.display = 'block';
        if (step === 'distribution') document.getElementById('questionDistributionStep').style.display = 'block';
        if (step === 'final') document.getElementById('genPaperBtn').style.display = 'block';
    }
}

function startAddQuestion() {
    document.getElementById('mainDashboard').style.display = 'none';
    document.getElementById('addQuestionForm').classList.add('active');
    currentStep.add = 'year';
    showStep('add');
}

function startGeneratePaper() {
    document.getElementById('mainDashboard').style.display = 'none';
    document.getElementById('generatePaperForm').classList.add('active');
    currentStep.generate = 'year';
    showStep('generate');
}

function goBack() {
    document.getElementById('addQuestionForm').classList.remove('active');
    document.getElementById('generatePaperForm').classList.remove('active');
    document.getElementById('paperPreview').classList.remove('active');
    document.getElementById('mainDashboard').style.display = 'grid';
    selectedData = {
        year: '',
        semester: '',
        subject: '',
        chapter: '',
        questionType: '',
        courseCode: '',
        examTime: 60,
        examType: '',
        selectedChapters: [],
        globalDistribution: {}
    };
}

function submitQuestion() {
    const questionText = document.getElementById('questionText').value.trim();
    const marks = parseInt(document.getElementById('questionMarks').value);

    if (!questionText || !marks) {
        showMessage('addMessage', 'Please fill all fields', 'error');
        return;
    }

    let mcqOptions = null;
    if (selectedData.questionType === 'MCQ') {
        const mcqA = document.getElementById('mcqA').value.trim();
        const mcqB = document.getElementById('mcqB').value.trim();
        const mcqC = document.getElementById('mcqC').value.trim();
        const mcqD = document.getElementById('mcqD').value.trim();

        if (!mcqA || !mcqB || !mcqC || !mcqD) {
            showMessage('addMessage', 'Please fill all MCQ options', 'error');
            return;
        }
        mcqOptions = [mcqA, mcqB, mcqC, mcqD];
    }

    const data = {
        subject: selectedData.subject,
        chapter: selectedData.chapter,
        question: questionText,
        marks: marks,
        difficulty: 'medium',
        year: selectedData.year,
        semester: selectedData.semester,
        questionType: selectedData.questionType,
        mcqOptions: mcqOptions
    };

    fetch('/add-question', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('addMessage', 'Question added successfully!', 'success');
                // Clear form
                document.getElementById('questionText').value = '';
                document.getElementById('questionMarks').value = '';
                document.getElementById('mcqA').value = '';
                document.getElementById('mcqB').value = '';
                document.getElementById('mcqC').value = '';
                document.getElementById('mcqD').value = '';
            } else {
                showMessage('addMessage', data.message || 'Error adding question', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('addMessage', 'Error adding question', 'error');
        });
}

function validateCourseCode() {
    const courseCode = document.getElementById('courseCode').value.trim();
    if (!courseCode) {
        showMessage('paperMessage', 'Please enter course code', 'error');
        return;
    }
    selectedData.courseCode = courseCode;
    currentStep.generate = 'time';
    showStep('generate');
}

function validateExamTime() {
    const examTime = parseInt(document.getElementById('examTime').value);
    if (!examTime || examTime < 30) {
        showMessage('paperMessage', 'Exam time must be at least 30 minutes', 'error');
        return;
    }
    selectedData.examTime = examTime;
    currentStep.generate = 'examType';
    showStep('generate');
}

function validateChapters() {
    const examType = selectedData.examType;
    const selectedCount = selectedData.selectedChapters.length;

    // Validation based on exam type
    if (examType === 'MSE') {
        if (selectedCount !== 3) {
            showMessage('paperMessage', `MSE requires exactly 3 chapters. You selected ${selectedCount}.`, 'error');
            return;
        }
    } else if (examType === 'ESE') {
        const allCheckboxes = document.querySelectorAll('.chapter-checkbox');
        if (selectedCount !== allCheckboxes.length) {
            showMessage('paperMessage', 'ESE requires all chapters to be selected', 'error');
            return;
        }
    } else {
        // Class Test
        if (selectedCount === 0) {
            showMessage('paperMessage', 'Please select at least one chapter', 'error');
            return;
        }
    }

    // Show question structure configuration
    buildQuestionStructure();
    currentStep.generate = 'distribution';
    showStep('generate');
}

function buildQuestionStructure() {
    const container = document.getElementById('chapterDistributionContainer');
    container.innerHTML = '';

    selectedData.selectedChapters.forEach((chapter, index) => {
        const questionNum = index + 1;

        const chapterDiv = document.createElement('div');
        chapterDiv.style.marginBottom = '25px';
        chapterDiv.style.padding = '20px';
        chapterDiv.style.background = 'white';
        chapterDiv.style.borderRadius = '8px';
        chapterDiv.style.border = '2px solid #e5e7eb';

        chapterDiv.innerHTML = `
            <h3 style="color: #2563eb; margin-bottom: 15px;">Q${questionNum}: ${chapter}</h3>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #374151;">
                    Q${questionNum}(A) - MCQ / One Sentence Questions
                </label>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                    <div>
                        <label style="font-size: 12px; color: #6b7280;">Number of sub-questions (i, ii, iii...)</label>
                        <input type="number" 
                               id="q${questionNum}a_count" 
                               min="0" 
                               max="10" 
                               value="3" 
                               style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #6b7280;">Marks per sub-question</label>
                        <input type="number" 
                               id="q${questionNum}a_marks" 
                               min="1" 
                               max="10" 
                               value="2" 
                               style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #6b7280;">Type</label>
                        <select id="q${questionNum}a_type" 
                                style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                            <option value="MCQ">MCQ</option>
                            <option value="One Sentence">One Sentence</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #374151;">
                    Q${questionNum}(B) - Long Answer Questions
                </label>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                    <div>
                        <label style="font-size: 12px; color: #6b7280;">Number of sub-questions (i, ii...)</label>
                        <input type="number" 
                               id="q${questionNum}b_count" 
                               min="0" 
                               max="10" 
                               value="2" 
                               style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #6b7280;">Marks per sub-question</label>
                        <input type="number" 
                               id="q${questionNum}b_marks" 
                               min="1" 
                               max="20" 
                               value="5" 
                               style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #6b7280;">Type</label>
                        <select id="q${questionNum}b_type" 
                                style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                            <option value="Long Answer">Long Answer</option>
                            <option value="Short Answer">Short Answer</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div style="padding: 10px; background: #f3f4f6; border-radius: 4px; font-size: 13px; color: #6b7280;">
                <strong>Total Marks for Q${questionNum}:</strong> 
                <span id="q${questionNum}_total">10</span> marks
            </div>
        `;

        container.appendChild(chapterDiv);

        // Add event listeners to calculate total marks
        setTimeout(() => {
            const aCount = document.getElementById(`q${questionNum}a_count`);
            const aMarks = document.getElementById(`q${questionNum}a_marks`);
            const bCount = document.getElementById(`q${questionNum}b_count`);
            const bMarks = document.getElementById(`q${questionNum}b_marks`);
            const totalSpan = document.getElementById(`q${questionNum}_total`);

            const updateTotal = () => {
                const total = (parseInt(aCount.value || 0) * parseInt(aMarks.value || 0)) +
                    (parseInt(bCount.value || 0) * parseInt(bMarks.value || 0));
                totalSpan.textContent = total;
            };

            aCount.addEventListener('input', updateTotal);
            aMarks.addEventListener('input', updateTotal);
            bCount.addEventListener('input', updateTotal);
            bMarks.addEventListener('input', updateTotal);
        }, 100);
    });

    // Add a button to proceed
    const nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.textContent = 'Generate Paper →';
    nextBtn.style.cssText = 'background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; padding: 15px 40px; border-radius: 8px; font-weight: 700; cursor: pointer; width: 100%; margin-top: 20px; font-size: 16px; transition: all 0.3s ease;';
    nextBtn.onclick = generatePaperWithStructure;
    container.appendChild(nextBtn);
}

function generatePaperWithStructure() {
    // Collect question structure data
    const questionStructure = [];
    let totalMarks = 0;

    selectedData.selectedChapters.forEach((chapter, index) => {
        const questionNum = index + 1;

        const aCount = parseInt(document.getElementById(`q${questionNum}a_count`).value || 0);
        const aMarks = parseInt(document.getElementById(`q${questionNum}a_marks`).value || 0);
        const aType = document.getElementById(`q${questionNum}a_type`).value;

        const bCount = parseInt(document.getElementById(`q${questionNum}b_count`).value || 0);
        const bMarks = parseInt(document.getElementById(`q${questionNum}b_marks`).value || 0);
        const bType = document.getElementById(`q${questionNum}b_type`).value;

        const questionTotal = (aCount * aMarks) + (bCount * bMarks);
        totalMarks += questionTotal;

        questionStructure.push({
            questionNumber: questionNum,
            chapter: chapter,
            partA: {
                count: aCount,
                marksEach: aMarks,
                type: aType,
                totalMarks: aCount * aMarks
            },
            partB: {
                count: bCount,
                marksEach: bMarks,
                type: bType,
                totalMarks: bCount * bMarks
            },
            totalMarks: questionTotal
        });
    });

    const data = {
        subject: selectedData.subject,
        selectedChapters: selectedData.selectedChapters.map(ch => ({ name: ch })),
        examType: selectedData.examType,
        courseCode: selectedData.courseCode,
        examTime: selectedData.examTime,
        questionStructure: questionStructure,
        totalMarks: totalMarks
    };

    fetch('/generate-paper', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPaper(data.paper);
                document.getElementById('generatePaperForm').classList.remove('active');
                document.getElementById('paperPreview').classList.add('active');
            } else {
                showMessage('paperMessage', data.message || 'Error generating paper', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('paperMessage', 'Error generating paper', 'error');
        });
}

function generatePaper() {
    if (selectedData.selectedChapters.length === 0) {
        showMessage('paperMessage', 'Please select at least one chapter', 'error');
        return;
    }

    const data = {
        subject: selectedData.subject,
        selectedChapters: selectedData.selectedChapters.map(ch => ({ name: ch })),
        examType: selectedData.examType,
        courseCode: selectedData.courseCode,
        examTime: selectedData.examTime,
        globalDistribution: selectedData.globalDistribution
    };

    fetch('/generate-paper', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPaper(data.paper);
                document.getElementById('generatePaperForm').classList.remove('active');
                document.getElementById('paperPreview').classList.add('active');
            } else {
                showMessage('paperMessage', data.message || 'Error generating paper', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('paperMessage', 'Error generating paper', 'error');
        });
}

function displayPaper(paper) {
    let html = `
        <div style="text-align: center; font-family: 'Times New Roman', serif; padding: 20px; border: 2px solid #000;">
            <h2 style="margin: 0; font-size: 18px; font-weight: bold;">P R Pote Patil College of Engineering & Management (PRPCEM)</h2>
            <h3 style="margin: 5px 0; font-size: 16px;">Amravati</h3>
            <h4 style="margin: 5px 0; font-size: 14px;">(An Autonomous Institute)</h4>
            <p style="margin: 10px 0; font-size: 13px;">Department: ExTC / AI&DS/ EE/ CIVIL / CSE / ME/CSE (AIML)</p>
            <p style="margin: 10px 0; font-size: 14px; font-weight: bold;">Mid Semester Examination-II (W-25)</p>
            
            <div style="display: flex; justify-content: space-between; margin-top: 15px; padding: 10px 0; border-top: 1px solid #000; border-bottom: 1px solid #000; text-align: left;">
                <div style="flex: 1;">
                    <p style="margin: 5px 0;"><strong>Course:</strong> ${paper.subject}</p>
                    <p style="margin: 5px 0;"><strong>Duration:</strong> ${paper.examTime} Min</p>
                </div>
                <div style="flex: 1; text-align: right;">
                    <p style="margin: 5px 0;"><strong>Course Code:</strong> ${paper.courseCode}</p>
                    <p style="margin: 5px 0;"><strong>Max. Marks:</strong> ${paper.total_marks}</p>
                </div>
            </div>
        </div>
        
        <div style="margin: 20px 0; padding: 15px; border: 1px solid #000; font-family: 'Times New Roman', serif;">
            <p style="font-weight: bold; margin-bottom: 10px; text-decoration: underline;">Important Instructions to the students</p>
            <p style="margin: 5px 0;"><strong>1)</strong> Figures to the right indicate the full marks.</p>
            <p style="margin: 5px 0;"><strong>2)</strong> Illustrate your answer whenever necessary with the help of neat sketches.</p>
            <p style="margin: 5px 0;"><strong>3)</strong> State your assumptions clearly whenever required</p>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; font-family: 'Times New Roman', serif; margin-top: 20px;">
            <thead>
                <tr style="border: 1px solid #000;">
                    <th style="border: 1px solid #000; padding: 8px; text-align: center; width: 80px;">Q No</th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: left;">Question</th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: center; width: 80px;">Marks</th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: center; width: 80px;">BTL</th>
                    <th style="border: 1px solid #000; padding: 8px; text-align: center; width: 80px;">CO</th>
                </tr>
            </thead>
            <tbody>
    `;

    // Check if we have structured questions
    if (paper.questionStructure && paper.questionStructure.length > 0) {
        paper.questionStructure.forEach((qStruct) => {
            const qNum = qStruct.questionNumber;

            // Part A
            if (qStruct.partA && qStruct.partA.count > 0) {
                const questions = qStruct.partA.questions || [];

                html += `
                    <tr style="border: 1px solid #000;">
                        <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top; font-weight: bold;">${qNum} A)</td>
                        <td style="border: 1px solid #000; padding: 8px; vertical-align: top;">
                            <p style="margin: 0 0 10px 0; font-weight: bold;">Solve the following questions.</p>
                `;

                for (let i = 0; i < qStruct.partA.count; i++) {
                    const subNum = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii'][i] || (i + 1);
                    const question = questions[i];
                    const questionText = question ? question.question_text : `[${qStruct.partA.type} Question not available]`;

                    html += `<p style="margin: 5px 0 5px 20px;"><strong>${subNum})</strong> ${questionText}`;

                    // Show MCQ options if available (all in one line)
                    if (question && question.question_type === 'MCQ' && question.mcq_options) {
                        try {
                            let options;
                            if (typeof question.mcq_options === 'string') {
                                options = JSON.parse(question.mcq_options);
                            } else {
                                options = question.mcq_options;
                            }

                            html += '<br><span style="margin-left: 20px;">';
                            // Handle both array and object formats
                            if (Array.isArray(options)) {
                                const optionsText = options.map((opt, idx) => {
                                    const letter = String.fromCharCode(65 + idx); // A, B, C, D
                                    return `${letter}) ${opt}`;
                                }).join('   ');
                                html += optionsText;
                            } else if (typeof options === 'object') {
                                const optionsText = Object.keys(options).map(key => {
                                    return `${key.toUpperCase()}) ${options[key]}`;
                                }).join('   ');
                                html += optionsText;
                            }
                            html += '</span>';
                        } catch (e) {
                            console.error('Error parsing MCQ options:', e);
                        }
                    }

                    html += `</p>`;
                }

                html += `
                        </td>
                        <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">
                `;

                for (let i = 0; i < qStruct.partA.count; i++) {
                    html += `<p style="margin: 15px 0;">${qStruct.partA.marksEach < 10 ? '0' : ''}${qStruct.partA.marksEach}</p>`;
                }

                html += `
                        </td>
                        <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">
                `;

                for (let i = 0; i < qStruct.partA.count; i++) {
                    html += `<p style="margin: 15px 0;">${i + 1}</p>`;
                }

                html += `
                        </td>
                        <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">
                `;

                for (let i = 0; i < qStruct.partA.count; i++) {
                    html += `<p style="margin: 15px 0;">3</p>`;
                }

                html += `
                        </td>
                    </tr>
                `;
            }

            // Part B
            if (qStruct.partB && qStruct.partB.count > 0) {
                const questions = qStruct.partB.questions || [];

                html += `
                    <tr style="border: 1px solid #000;">
                        <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top; font-weight: bold;">${qNum} B)</td>
                        <td style="border: 1px solid #000; padding: 8px; vertical-align: top;">
                            <p style="margin: 0 0 10px 0; font-weight: bold;">Solve any two questions of the following</p>
                `;

                for (let i = 0; i < qStruct.partB.count; i++) {
                    const subNum = ['i', 'ii', 'iii', 'iv', 'v', 'vi'][i] || (i + 1);
                    const question = questions[i];
                    const questionText = question ? question.question_text : `[${qStruct.partB.type} Question not available]`;

                    html += `<p style="margin: 5px 0 5px 20px;"><strong>${subNum})</strong> ${questionText}`;

                    // Show MCQ options if available (all in one line)
                    if (question && question.question_type === 'MCQ' && question.mcq_options) {
                        try {
                            let options;
                            if (typeof question.mcq_options === 'string') {
                                options = JSON.parse(question.mcq_options);
                            } else {
                                options = question.mcq_options;
                            }

                            html += '<br><span style="margin-left: 20px;">';
                            // Handle both array and object formats
                            if (Array.isArray(options)) {
                                const optionsText = options.map((opt, idx) => {
                                    const letter = String.fromCharCode(65 + idx); // A, B, C, D
                                    return `${letter}) ${opt}`;
                                }).join('   ');
                                html += optionsText;
                            } else if (typeof options === 'object') {
                                const optionsText = Object.keys(options).map(key => {
                                    return `${key.toUpperCase()}) ${options[key]}`;
                                }).join('   ');
                                html += optionsText;
                            }
                            html += '</span>';
                        } catch (e) {
                            console.error('Error parsing MCQ options:', e);
                        }
                    }

                    html += `</p>`;
                }

                html += `
                        </td>
                        <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">
                `;

                for (let i = 0; i < qStruct.partB.count; i++) {
                    html += `<p style="margin: 15px 0;">${qStruct.partB.marksEach < 10 ? '0' : ''}${qStruct.partB.marksEach}</p>`;
                }

                html += `
                        </td>
                        <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">
                `;

                for (let i = 0; i < qStruct.partB.count; i++) {
                    html += `<p style="margin: 15px 0;">${i + 3}</p>`;
                }

                html += `
                        </td>
                        <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">
                `;

                for (let i = 0; i < qStruct.partB.count; i++) {
                    html += `<p style="margin: 15px 0;">3</p>`;
                }

                html += `
                        </td>
                    </tr>
                `;
            }
        });
    } else if (paper.questions && paper.questions.length > 0) {
        // Fallback to old format if no structure
        paper.questions.forEach((question, index) => {
            html += `
                <tr style="border: 1px solid #000;">
                    <td style="border: 1px solid #000; padding: 8px; text-align: center;">${index + 1}</td>
                    <td style="border: 1px solid #000; padding: 8px;">${question.question_text}</td>
                    <td style="border: 1px solid #000; padding: 8px; text-align: center;">${question.marks < 10 ? '0' : ''}${question.marks}</td>
                    <td style="border: 1px solid #000; padding: 8px; text-align: center;">${index + 1}</td>
                    <td style="border: 1px solid #000; padding: 8px; text-align: center;">3</td>
                </tr>
            `;

            if (question.question_type === 'MCQ' && question.mcq_options) {
                try {
                    const options = JSON.parse(question.mcq_options);
                    html += '<p style="margin-top: 10px;"><strong>Options:</strong></p><ul style="margin-left: 20px;">';
                    options.forEach((opt, i) => {
                        html += `<li>${String.fromCharCode(65 + i)}: ${opt}</li>`;
                    });
                    html += '</ul>';
                } catch (e) {
                    console.error('Error parsing MCQ options:', e);
                }
            }

        });
    } else {
        html += `
            <tr style="border: 1px solid #000;">
                <td colspan="5" style="border: 1px solid #000; padding: 20px; text-align: center;">No questions in this paper.</td>
            </tr>
        `;
    }

    html += `
            </tbody>
        </table>
    `;

    document.getElementById('paperContent').innerHTML = html;
}

function downloadPaper() {
    const element = document.getElementById('paperContent');
    const opt = {
        margin: 10,
        filename: 'question_paper.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
    };
    html2pdf().set(opt).from(element).save();
}

function printPaper() {
    const element = document.getElementById('paperContent');
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Print Paper</title></head><body>');
    printWindow.document.write(element.innerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

function showMessage(elementId, message, type) {
    const messageElement = document.getElementById(elementId);
    messageElement.textContent = message;
    messageElement.className = `message ${type}`;

    setTimeout(() => {
        messageElement.className = 'message';
    }, 5000);
}
