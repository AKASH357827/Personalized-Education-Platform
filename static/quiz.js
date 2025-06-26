async function renderQuestions() {
    const selectedSubject = document.getElementById('subject').value;
    if (!selectedSubject) {
        console.warn('No topic selected.');
        return;
    }

    const questionsContainer = document.getElementById('questions-container');
    const submitBtn = document.getElementById('submitBtn');
    questionsContainer.innerHTML = '';

    try {
        console.log("quiz selected");
        let jsonFile = "static/question.json";  // Default
        if (selectedSubject.startsWith("custom_", 0)) {
            jsonFile = "static/custom_quiz.json"; // Custom json quiz file
            console.log("Custom quiz selected");
        }
        const response = await fetch(jsonFile); // Use correct file.
        const data = await response.json();
        const questions = data[selectedSubject];

        if (!questions) {
            console.error("No questions found for subject:", selectedSubject);
            return;
        }

        const selectedQuestions = getRandomQuestions(questions, 10);

        selectedQuestions.forEach((question, index) => {
            const questionElement = document.createElement('div');
            questionElement.classList.add('mb-8', 'p-6', 'bg-gray-50', 'rounded-lg');

            let optionsHTML = '<div class="space-y-3 mt-4">';
            question.options.forEach(option => {
                optionsHTML += `
                    <div class="flex items-center">
                        <input type="radio"
                               id="${question.id}_${option}"
                               name="${question.id}"
                               value="${option}"
                               required
                               class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500">
                        <label for="${question.id}_${option}"
                               class="ml-3 text-gray-700">
                            ${option}
                        </label>
                    </div>
                `;
            });
            optionsHTML += '</div>';

            questionElement.innerHTML = `
                <p class="text-lg font-medium text-gray-900">
                    ${index + 1}. ${question.question}
                </p>
                ${optionsHTML}
            `;

            questionsContainer.appendChild(questionElement);
        });

        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    } catch (error) {
        console.error('Error loading questions:', error);
    }
}

function getRandomQuestions(questions, count) {
    const shuffled = [...questions].sort(() => 0.5 - Math.random());
    console.log(shuffled);

    return shuffled.slice(0, count);
}

const subjectButtons1 = document.querySelectorAll('.subject-btn');
subjectButtons1.forEach(button => {
    button.addEventListener('click', function() {
        const topic = this.dataset.topic;
        console.log("This is the current selected: " + topic) // Check the values
        document.getElementById('subject').value = topic;
        
        renderQuestions() // Add renderQuestions() calls
        // Update button styles
        subjectButtons1.forEach(btn => {
            btn.classList.remove('bg-indigo-600', 'text-white');
            btn.classList.add('bg-indigo-100', 'text-indigo-600');
        });
        this.classList.remove('bg-indigo-100', 'text-indigo-600');
        this.classList.add('bg-indigo-600', 'text-white');
    });
});