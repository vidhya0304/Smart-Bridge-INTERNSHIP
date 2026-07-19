const quizSetupScreen = document.getElementById('quizSetupScreen');
const quizPlayScreen = document.getElementById('quizPlayScreen');
const quizResultScreen = document.getElementById('quizResultScreen');
const loadingOverlay = document.getElementById('quizLoadingOverlay');

const quizTopicInput = document.getElementById('quizTopicInput');
const generateQuizBtn = document.getElementById('generateQuizBtn');
const useLocalT5 = document.getElementById('quizUseLocalT5');
const numQuestions = document.getElementById('numQuestions');

const quizPlayTopic = document.getElementById('quizPlayTopic');
const questionTracker = document.getElementById('questionTracker');
const timerVal = document.getElementById('timerVal');
const progressBarFill = document.getElementById('progressBarFill');
const quizQuestionText = document.getElementById('quizQuestionText');
const quizOptionsList = document.getElementById('quizOptionsList');
const quizAnswerFeedback = document.getElementById('quizAnswerFeedback');
const feedbackTitle = document.getElementById('feedbackTitle');
const feedbackText = document.getElementById('feedbackText');
const nextQuestionBtn = document.getElementById('nextQuestionBtn');

const finalScoreVal = document.getElementById('finalScoreVal');
const finalPercentage = document.getElementById('finalPercentage');
const finalTimeVal = document.getElementById('finalTimeVal');
const restartQuizBtn = document.getElementById('restartQuizBtn');

let activeQuiz = null;
let currentQuestionIndex = 0;
let score = 0;
let timerInterval = null;
let secondsElapsed = 0;
let answerSelected = false;

generateQuizBtn.addEventListener('click', startQuizGeneration);
nextQuestionBtn.addEventListener('click', proceedToNextQuestion);
restartQuizBtn.addEventListener('click', resetQuizToSetup);

function setTopic(topic) {
    quizTopicInput.value = topic;
    startQuizGeneration();
}

async function startQuizGeneration() {
    const topic = quizTopicInput.value.trim();
    if (!topic) return;
    
    // Show spinner
    loadingOverlay.style.display = 'flex';
    
    try {
        const response = await fetch('/api/quiz', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: topic,
                count: parseInt(numQuestions.value),
                use_local: useLocalT5.checked
            })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to generate quiz');
        }
        
        const data = await response.json();
        activeQuiz = data;
        
        // Initialize Quiz Play State
        currentQuestionIndex = 0;
        score = 0;
        secondsElapsed = 0;
        answerSelected = false;
        
        quizPlayTopic.textContent = `Topic: ${data.topic}`;
        
        // Hide setups, display plays
        loadingOverlay.style.display = 'none';
        quizSetupScreen.style.display = 'none';
        quizPlayScreen.style.display = 'flex';
        
        // Start timers
        startTimer();
        
        // Render first question
        renderQuestion();
        
    } catch (err) {
        loadingOverlay.style.display = 'none';
        alert(`Error generating quiz: ${err.message}`);
    }
}

function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        secondsElapsed++;
        const mins = Math.floor(secondsElapsed / 60).toString().padStart(2, '0');
        const secs = (secondsElapsed % 60).toString().padStart(2, '0');
        timerVal.textContent = `${mins}:${secs}`;
    }, 1000);
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
}

function renderQuestion() {
    if (!activeQuiz || !activeQuiz.questions || activeQuiz.questions.length === 0) return;
    
    answerSelected = false;
    nextQuestionBtn.style.display = 'none';
    quizAnswerFeedback.style.display = 'none';
    
    const totalQ = activeQuiz.questions.length;
    questionTracker.textContent = `Question ${currentQuestionIndex + 1} of ${totalQ}`;
    
    // Progress bar fill
    const fillPercent = ((currentQuestionIndex) / totalQ) * 100;
    progressBarFill.style.style = `width: ${fillPercent}%;`; // Wait, CSS style setting
    progressBarFill.style.width = `${fillPercent}%`;
    
    const questionObj = activeQuiz.questions[currentQuestionIndex];
    quizQuestionText.textContent = questionObj.question;
    
    // Render options buttons
    quizOptionsList.innerHTML = '';
    questionObj.options.forEach(opt => {
        const btn = document.createElement('button');
        btn.classList.add('quiz-option');
        btn.textContent = opt;
        btn.addEventListener('click', () => handleOptionSelection(btn, opt, questionObj));
        quizOptionsList.appendChild(btn);
    });
}

function handleOptionSelection(selectedBtn, selectedText, questionObj) {
    if (answerSelected) return; // Lock selections
    answerSelected = true;
    
    const correctVal = questionObj.correct_answer;
    
    // Check if correct
    const isCorrect = (selectedText.toLowerCase().trim() === correctVal.toLowerCase().trim());
    
    if (isCorrect) {
        score++;
        selectedBtn.classList.add('correct');
        feedbackTitle.textContent = 'Correct!';
        feedbackTitle.style.color = '#047857';
        quizAnswerFeedback.style.borderLeftColor = '#10b981';
        quizAnswerFeedback.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
    } else {
        selectedBtn.classList.add('incorrect');
        feedbackTitle.textContent = 'Incorrect';
        feedbackTitle.style.color = '#b91c1c';
        quizAnswerFeedback.style.borderLeftColor = '#ef4444';
        quizAnswerFeedback.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
        
        // Find correct button and color it green
        const optionButtons = quizOptionsList.querySelectorAll('.quiz-option');
        optionButtons.forEach(btn => {
            if (btn.textContent.toLowerCase().trim() === correctVal.toLowerCase().trim()) {
                btn.classList.add('correct');
            }
        });
    }
    
    feedbackText.textContent = questionObj.explanation;
    quizAnswerFeedback.style.display = 'block';
    
    // Show Next Question button
    nextQuestionBtn.style.display = 'inline-flex';
}

function proceedToNextQuestion() {
    currentQuestionIndex++;
    if (currentQuestionIndex < activeQuiz.questions.length) {
        renderQuestion();
    } else {
        showResults();
    }
}

function showResults() {
    stopTimer();
    quizPlayScreen.style.display = 'none';
    quizResultScreen.style.display = 'flex';
    
    // Progress fill to 100%
    progressBarFill.style.width = '100%';
    
    const totalQ = activeQuiz.questions.length;
    finalScoreVal.textContent = `${score}/${totalQ}`;
    
    const percentage = Math.round((score / totalQ) * 100);
    finalPercentage.textContent = `Score: ${percentage}%`;
    
    const mins = Math.floor(secondsElapsed / 60).toString().padStart(2, '0');
    const secs = (secondsElapsed % 60).toString().padStart(2, '0');
    finalTimeVal.textContent = `${mins}:${secs}`;
}

function resetQuizToSetup() {
    quizResultScreen.style.display = 'none';
    quizSetupScreen.style.display = 'flex';
    quizTopicInput.value = '';
    activeQuiz = null;
}
