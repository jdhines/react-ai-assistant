export function Header() {
  return (
    <header className="flex gap-9 p-4 bg-blue-800">
      <div className="max-w-[100vw]">
        <img src="/HQ-icon.svg" alt="HQ Icon" className="h-8 w-8 inline-block" />
        <span className="text-white">HQ Assistant</span>
      </div>
    </header>
  )
}