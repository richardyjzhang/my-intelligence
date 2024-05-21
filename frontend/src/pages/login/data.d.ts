declare namespace API {
  type LoginUser = {
    username: string;
    password: string;
  };

  type LoginResult = {
    success: boolean;
    message: string;
  };
}
