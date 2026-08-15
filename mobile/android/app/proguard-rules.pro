# GULA Android release rules
# SQLCipher resolves native/JNI classes by name.
-keep,includedescriptorclasses class net.zetetic.database.** { *; }
-keep,includedescriptorclasses interface net.zetetic.database.** { *; }

# Retrofit/Moshi models use annotations and generated adapters.
-keepattributes RuntimeVisibleAnnotations,RuntimeInvisibleAnnotations,RuntimeVisibleParameterAnnotations,RuntimeInvisibleParameterAnnotations,AnnotationDefault
-if @com.squareup.moshi.JsonClass class **
-keep class <1>JsonAdapter { <init>(...); }

# Room generated implementation is loaded by generated name.
-keep class **_Impl { *; }
