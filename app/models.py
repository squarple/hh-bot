from dataclasses import dataclass

class BotUser:
  def __init__(self, chat_id: int, username: str, password: str):
    self.chat_id = chat_id
    self.username = username
    self.password = password

  def __repr__(self):
    return f"bot_user(chat_id={self.chat_id}, username='{self.username}', password='{self.password}')"


@dataclass
class User :
  accessToken     : str
  refreshToken    : str
  userId          : int
  cohortId        : int
  role            : str
  username        : str
  name            : str
  surname         : str
  email           : str
  gitlabUsername  : str
  mmUsername      : str

@dataclass
class Homework :
  id                  : int
  name                : str
  topic               : str
  description         : str
  sourceCommitId      : str
  departments         : list
  author              : dict
  lecture             : dict
  repositoryLink      : str
  startDate           : str
  completionDeadline  : str
  status              : str
  reviewDuration      : int

@dataclass
class Review :
  reviewId        : int
  status          : str
  projectId       : int
  sourceCommitId  : str
  commitId        : str
  reviewAttempts  : dict

def json_to_review(json : dict) -> Review :
  if json is not None:
    return Review(
      reviewId        = json.get('reviewId'),
      status          = json.get('status'),
      projectId       = json.get('projectId'),
      sourceCommitId  = json.get('sourceCommitId'),
      commitId        = json.get('commitId'),
      reviewAttempts  = json.get('reviewAttempts'),
    )

def json_to_homework(json : dict) -> Homework :
  if json is not None:
    return Homework(
      id                  = json.get('id'),
      name                = json.get('name'),
      topic               = json.get('topic'),
      description         = json.get('description'),
      sourceCommitId      = json.get('sourceCommitId'),
      departments         = json.get('departments'),
      author              = json.get('author'),
      lecture             = json.get('lecture'),
      repositoryLink      = json.get('repositoryLink'),
      startDate           = json.get('startDate'),
      completionDeadline  = json.get('completionDeadline'),
      status              = json.get('status'),
      reviewDuration      = json.get('reviewDuration'),
    )

def json_to_user(json : dict) -> User :
  if json is not None:
    return User(
      accessToken     = json.get('accessToken'),
      refreshToken    = json.get('refreshToken'),
      userId          = json.get('userId'),
      cohortId        = json.get('cohortId'),
      role            = json.get('role'),
      username        = json.get('username'),
      name            = json.get('name'),
      surname         = json.get('surname'),
      email           = json.get('email'),
      gitlabUsername  = json.get('gitlabUsername'),
      mmUsername      = json.get('mmUsername'),
    )
