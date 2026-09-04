import React from 'react';
import { Story } from '../types';
import { StoryCard } from './StoryCard';

interface StoryGridProps {
  stories: Story[];
  onSelectStory: (storyId: string) => void;
}

export const StoryGrid: React.FC<StoryGridProps> = ({ stories, onSelectStory }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {stories.map((story) => (
        <StoryCard key={story.id} story={story} onSelectStory={onSelectStory} />
      ))}
    </div>
  );
};

