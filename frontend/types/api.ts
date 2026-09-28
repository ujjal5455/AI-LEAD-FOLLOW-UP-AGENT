// Shapes of the data returned by the backend API (see backend/app/schemas).

export type User = {
  id: string;
  email: string;
  full_name: string | null;
};

export type BusinessSummary = {
  id: string;
  name: string;
  industry: string | null;
  timezone: string;
};

export type Session = {
  user: User;
  business: BusinessSummary;
};
