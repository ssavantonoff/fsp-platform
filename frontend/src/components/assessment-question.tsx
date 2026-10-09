import { competencyLabels } from "@/assessment";
import type { AssessmentQuestion as Question } from "@/assessment";

export function AssessmentQuestion({
  question,
  selected,
  disabled,
  onSelect,
}: {
  question: Question;
  selected: string | null;
  disabled: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <fieldset disabled={disabled} className="assessment-options" aria-describedby={`assessment-prompt-${question.attempt_question_id} assessment-option-hint-${question.attempt_question_id}`}>
      <legend>
        {competencyLabels[question.competency] ?? question.competency}
      </legend>
      <p id={`assessment-prompt-${question.attempt_question_id}`} className="question-prompt">{question.prompt}</p>
      <p id={`assessment-option-hint-${question.attempt_question_id}`} className="hint">Выберите один вариант. Ответ сохраняется автоматически.</p>
      {question.options.map((option) => (
        <label className="assessment-option" data-selected={selected === option.id} key={option.id}>
          <input
            type="radio"
            name={`question-${question.attempt_question_id}`}
            value={option.id}
            checked={selected === option.id}
            onChange={() => onSelect(option.id)}
          />
          <span>{option.text}</span>
        </label>
      ))}
    </fieldset>
  );
}
