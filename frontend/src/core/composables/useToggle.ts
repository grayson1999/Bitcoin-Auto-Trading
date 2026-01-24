import { useState, useCallback } from 'react'

/**
 * Toggle boolean state
 * @param initialValue - Initial value
 * @returns [value, toggle, setValue]
 */
export function useToggle(
  initialValue = false
): [boolean, () => void, (value: boolean) => void] {
  const [value, setValue] = useState(initialValue)

  const toggle = useCallback(() => {
    setValue((prev) => !prev)
  }, [])

  return [value, toggle, setValue]
}

export default useToggle
