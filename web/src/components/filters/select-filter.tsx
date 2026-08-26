import styles from "./filters.module.css";

export type SelectFilterOption = {
  value: string;
  label: string;
};

type SelectFilterProps = {
  id: string;
  label: string;
  value: string;
  options: SelectFilterOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
};

export function SelectFilter({
  id,
  label,
  value,
  options,
  onChange,
  disabled = false,
}: SelectFilterProps) {
  return (
    <label
      className={styles.field}
      htmlFor={id}
    >
      <span className={styles.label}>
        {label}
      </span>

      <select
        id={id}
        className={styles.select}
        value={value}
        disabled={disabled}
        onChange={(event) =>
          onChange(
            event.target.value,
          )
        }
      >
        {options.map(
          (option) => (
            <option
              key={option.value}
              value={option.value}
            >
              {option.label}
            </option>
          ),
        )}
      </select>
    </label>
  );
}