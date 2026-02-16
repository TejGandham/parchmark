import React, { type ReactNode } from 'react';
import { Text } from '@chakra-ui/react';

export const VIRTUALIZATION_THRESHOLD = 50;
export const PALETTE_ITEM_HEIGHT = 40;
export const VIRTUAL_LIST_HEIGHT = 320;

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function highlightKeyword(text: string, keyword: string): ReactNode {
  if (!keyword) return text;
  const escaped = escapeRegex(keyword);
  const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
  return parts.map((part, i) =>
    part.toLowerCase() === keyword.toLowerCase() ? (
      <Text as="strong" key={i} fontWeight="bold" color="primary.700">
        {part}
      </Text>
    ) : (
      part
    )
  );
}
