import { useId, cloneElement, isValidElement } from 'react'

function FormField({ label, hint, children, required = false }) {
  const id = useId()
  const child = isValidElement(children) && !children.props.id
    ? cloneElement(children, { id })
    : children

  return (
    <div className="form-group">
      <label className="form-label" htmlFor={isValidElement(children) ? (children.props.id || id) : undefined}>
        {label}
        {required && <span className="required-mark">*</span>}
      </label>
      {child}
      {hint && <div className="form-hint">{hint}</div>}
    </div>
  )
}

export default FormField
