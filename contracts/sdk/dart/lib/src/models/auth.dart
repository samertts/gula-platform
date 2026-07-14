import 'package:json_annotation/json_annotation.dart';

part 'auth.g.dart';

@JsonSerializable()
class LoginRequest {
  final String email;
  final String password;

  const LoginRequest({required this.email, required this.password});

  factory LoginRequest.fromJson(Map<String, dynamic> json) => _$LoginRequestFromJson(json);
  Map<String, dynamic> toJson() => _$LoginRequestToJson(this);
}

@JsonSerializable()
class LoginResponse {
  final String token;
  final String refreshToken;
  final String tokenType;
  final LoginUser user;

  const LoginResponse({
    required this.token,
    required this.refreshToken,
    required this.tokenType,
    required this.user,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) => _$LoginResponseFromJson(json);
  Map<String, dynamic> toJson() => _$LoginResponseToJson(this);
}

@JsonSerializable()
class LoginUser {
  final int id;
  final String name;
  final String email;
  final String role;
  final int? labId;
  final String? labName;

  const LoginUser({
    required this.id,
    required this.name,
    required this.email,
    required this.role,
    this.labId,
    this.labName,
  });

  factory LoginUser.fromJson(Map<String, dynamic> json) => _$LoginUserFromJson(json);
  Map<String, dynamic> toJson() => _$LoginUserToJson(this);
}

@JsonSerializable()
class RegisterRequest {
  final String email;
  final String password;
  final String fullName;
  final String? phone;
  final String? role;
  final int? labId;

  const RegisterRequest({
    required this.email,
    required this.password,
    required this.fullName,
    this.phone,
    this.role,
    this.labId,
  });

  factory RegisterRequest.fromJson(Map<String, dynamic> json) => _$RegisterRequestFromJson(json);
  Map<String, dynamic> toJson() => _$RegisterRequestToJson(this);
}

@JsonSerializable()
class RefreshTokenRequest {
  final String refreshToken;

  const RefreshTokenRequest({required this.refreshToken});

  factory RefreshTokenRequest.fromJson(Map<String, dynamic> json) =>
      _$RefreshTokenRequestFromJson(json);
  Map<String, dynamic> toJson() => _$RefreshTokenRequestToJson(this);
}

@JsonSerializable()
class RefreshTokenResponse {
  final String token;
  final String refreshToken;
  final String tokenType;

  const RefreshTokenResponse({
    required this.token,
    required this.refreshToken,
    required this.tokenType,
  });

  factory RefreshTokenResponse.fromJson(Map<String, dynamic> json) =>
      _$RefreshTokenResponseFromJson(json);
  Map<String, dynamic> toJson() => _$RefreshTokenResponseToJson(this);
}
