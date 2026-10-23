import React from 'react';

interface ShellPageProps {
  title: string;
  description: string;
}

export function ShellPage({ title, description }: ShellPageProps) {
  return (
    <div className="p-6 flex flex-col items-center justify-center h-full text-center space-y-4">
      <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
        <span className="text-2xl">🛠️</span>
      </div>
      <h1 className="text-2xl font-bold">{title}</h1>
      <p className="text-muted-foreground max-w-md">
        {description} This feature is part of a later phase and will be implemented soon.
      </p>
    </div>
  );
}
