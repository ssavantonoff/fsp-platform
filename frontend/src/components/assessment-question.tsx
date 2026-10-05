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
    <fieldset disabled={disabled} className="assessment-options">
      <legend>
        {competencyLabels[question.competency] ?? question.competency}
      </legend>
      <p className="question-prompt">{question.prompt}</p>
      {question.options.map((option) => (
        <label className="assessment-option" key={option.id}>
          <input
            type="radio"
            name={`question-${question.attempt_question_id}`}
            checked={selected === option.id}
            onChange={() => onSelect(option.id)}
          />
          <span>{option.text}</span>
        </label>
      ))}
    </fieldset>
  );
}
